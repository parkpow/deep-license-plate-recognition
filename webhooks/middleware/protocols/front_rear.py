"""
Front-Rear Stream Middleware Protocol

Receives webhooks from paired front/rear cameras, validates license plates against
Front-Rear Vehicle Database, checks make/model confidence, and triggers alerts for:
- Alert #1: Plates not in Front-Rear DB (plate_mismatch)
- Alert #2: Missing rear plates when camera is online (no_rear_plate)
- Alert #3: Make/model mismatches with confidence thresholds (make_model_mismatch)
- Alert #4: Camera offline detection (camera_offline)

Event Buffering & Pairing:
- Buffers events from each camera with configurable time window (default 30s)
- Processes pairs when both cameras detect within the time window
- Handles unpaired events in two scenarios:
  * Expiry: Event exceeds time window without pairing (2x time window)
  * Overwrite: New vehicle detected before previous pairing completes

Resilience & Offline Camera Handling:
- Validates single-camera events against database when pair camera is offline
- Sends camera_offline alert (Alert #4) instead of no_rear_plate when rear camera offline
- Forwards data from available camera (prefers rear, falls back to front)

Data Forwarding:
- Forwards rear camera data to ParkPow after validation (preferred)
- Falls back to front camera data if rear camera is unavailable
- Ensures no data loss even with single camera operation
"""

import asyncio
import csv
import json
import logging
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any

import aiohttp

from protocols.shared.utils import get_header

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@dataclass
class CameraEvent:
    """Structured webhook event from a camera."""

    camera_id: str
    results: list[dict[str, Any]]
    timestamp: str
    timestamp_local: str | None
    timestamp_unix: float
    original_json_data: dict[str, Any]
    original_files: Any


@dataclass
class CameraPair:
    """
    Paired front/rear camera configuration with runtime event buffering.

    Combines static configuration (which cameras form a pair) with runtime state
    (pending events from those cameras awaiting pairing).

    Attributes:
        front: Camera ID for the front camera
        rear: Camera ID for the rear camera
        description: Human-readable description of the camera pair location
        front_event: Pending event from front camera (None if no event buffered)
        rear_event: Pending event from rear camera (None if no event buffered)
    """

    front: str
    rear: str
    description: str
    front_event: CameraEvent | None = None
    rear_event: CameraEvent | None = None

    @property
    def id(self) -> str:
        return f"{self.front}:{self.rear}"


csv_vehicles: dict[str, dict[str, str]] = {}  # plate -> {make, model}
camera_pairs: list[CameraPair] = []
config: dict[str, Any] = {}
pair_locks: dict[str, Lock] = defaultdict(lambda: Lock())

_config_cache: dict[str, Any] | None = None
_config_last_load: float = 0.0

_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_aiohttp_session: aiohttp.ClientSession | None = None


def _load_config() -> dict[str, Any]:
    """Load configuration from JSON file with hot-reload support."""
    global _config_cache, _config_last_load

    config_path = "protocols/config/front_rear_config.json"

    try:
        file_mtime = os.path.getmtime(config_path)
        if _config_cache and file_mtime <= _config_last_load:
            return _config_cache

        with open(config_path) as f:
            config_data: dict[str, Any] = json.load(f)

        _config_cache = config_data
        _config_last_load = file_mtime

        logging.info(f"Loaded Front-Rear configuration from {config_path}")
        return config_data

    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in configuration file: {e}")
        return {}


def _load_vehicles_csv() -> None:
    """Load Front-Rear Vehicle Database CSV into memory for fast lookups."""
    global csv_vehicles, config

    config = _load_config()
    csv_path = config.get("front_rear_csv_path", "front_rear.csv")

    try:
        csv_vehicles.clear()
        total_rows = 0
        skipped = 0

        # First pass: Identify duplicates and invalid plates
        plate_occurrences: dict[str, list[dict[str, str]]] = {}
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_rows += 1
                plate = row["LICENSE_PLATE"].strip().upper()

                if plate == "99":
                    skipped += 1
                    continue

                if plate not in plate_occurrences:
                    plate_occurrences[plate] = []
                plate_occurrences[plate].append(
                    {
                        "make": row["MAKE"].strip().upper(),
                        "model": row["MODEL"].strip().upper(),
                    }
                )

        # Second pass: Only load plates that appear exactly once
        duplicates = 0
        for plate, occurrences in plate_occurrences.items():
            if len(occurrences) == 1:
                csv_vehicles[plate] = occurrences[0]
            else:
                duplicates += len(occurrences)

        if not csv_vehicles:
            logging.error(f"Front-Rear CSV file is empty: {csv_path}")
            raise ValueError(
                "Front-Rear database is empty, cannot operate without vehicle data"
            )

        logging.info(
            f"Loaded {len(csv_vehicles)} vehicles from Front-Rear database "
            f"({total_rows} rows, {duplicates} duplicates skipped, {skipped} invalid plates skipped)"
        )

    except FileNotFoundError:
        logging.error(f"Front-Rear CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading Front-Rear CSV: {e}")
        raise


async def _create_aiohttp_session() -> aiohttp.ClientSession:
    """Create aiohttp ClientSession inside the event loop."""
    # Create session with default timeout to avoid "Timeout context manager should be used inside a task" error
    timeout = aiohttp.ClientTimeout(total=30)
    return aiohttp.ClientSession(timeout=timeout)


def _run_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Run the asyncio event loop in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def initialize() -> None:
    """
    Initialize Front-Rear middleware at startup.

    Loads:
    - Front-Rear Vehicle Database (CSV)
    - Configuration (camera pairs, thresholds, endpoints)
    - Schedules periodic cleanup of expired buffered events
    - Starts asyncio event loop for non-blocking API calls
    """
    global camera_pairs, config, _loop, _loop_thread, _aiohttp_session

    _load_vehicles_csv()
    config = _load_config()
    camera_pairs = [CameraPair(**pair) for pair in config.get("camera_pairs", [])]
    parkpow_config = config.get("parkpow", {})
    alert_endpoint = parkpow_config.get("alert_endpoint")
    webhook_endpoint = parkpow_config.get("webhook_endpoint")
    token = parkpow_config.get("token")

    if not camera_pairs:
        logging.error("No camera pairs configured in Front-Rear middleware")
        raise ValueError("Front-Rear middleware requires at least one camera pair")

    if not alert_endpoint:
        logging.error("ParkPow alert_endpoint not configured")
        raise ValueError("Front-Rear middleware requires parkpow.alert_endpoint")

    if not webhook_endpoint:
        logging.error("ParkPow webhook_endpoint not configured")
        raise ValueError("Front-Rear middleware requires parkpow.webhook_endpoint")

    if not token:
        logging.error("ParkPow token not configured")
        raise ValueError("Front-Rear middleware requires parkpow.token")

    _loop = asyncio.new_event_loop()
    _loop_thread = threading.Thread(target=_run_event_loop, args=(_loop,), daemon=True)
    _loop_thread.start()

    if _loop is not None:
        future = asyncio.run_coroutine_threadsafe(_create_aiohttp_session(), _loop)
        _aiohttp_session = future.result(timeout=5)

    logging.info(
        f"Initialized Front-Rear middleware with {len(camera_pairs)} camera pairs and asyncio event loop"
    )

    cleanup_thread = threading.Thread(target=_cleanup_task_loop, daemon=True)
    cleanup_thread.start()


def shutdown() -> None:
    """
    Shutdown Front-Rear middleware and cleanup resources.

    Closes aiohttp session and stops the asyncio event loop.
    """
    global _loop, _loop_thread, _aiohttp_session

    logging.info("Front-Rear middleware shutdown initiated...")

    # Close aiohttp session
    if _aiohttp_session is not None and _loop is not None:
        logging.info("Closing aiohttp session...")
        try:
            future = asyncio.run_coroutine_threadsafe(_aiohttp_session.close(), _loop)
            future.result(timeout=5)
            logging.info("Aiohttp session closed successfully")
        except TimeoutError:
            logging.warning("Timeout while closing aiohttp session")
        except Exception as e:
            logging.error(f"Error closing aiohttp session: {e}")
        finally:
            _aiohttp_session = None
    elif _aiohttp_session is None:
        logging.debug("Aiohttp session already closed or not initialized")

    # Stop event loop
    if _loop is not None:
        logging.info("Stopping asyncio event loop...")
        try:
            _loop.call_soon_threadsafe(lambda: _loop.stop() if _loop else None)
            if _loop_thread is not None and _loop_thread.is_alive():
                logging.debug("Waiting for event loop thread to finish...")
                _loop_thread.join(timeout=5)
                if _loop_thread.is_alive():
                    logging.warning("Event loop thread did not stop within timeout")
            _loop.close()
            logging.info("Asyncio event loop stopped successfully")
        except Exception as e:
            logging.error(f"Error stopping asyncio event loop: {e}")
        finally:
            _loop = None
            _loop_thread = None
    else:
        logging.debug("Asyncio event loop already stopped or not initialized")

    logging.info("Front-Rear middleware shutdown complete")


def _cleanup_task_loop() -> None:
    """Daemon thread that periodically runs cleanup of expired events."""
    while True:
        try:
            # Reload config on each iteration for hot reload support
            current_config = _load_config()
            cleanup_interval = current_config.get("pairing", {}).get(
                "cleanup_interval_seconds", 60
            )
            _cleanup_expired_events()
        except Exception as e:
            logging.error(f"Error in cleanup task: {e}")
            cleanup_interval = 60  # Default fallback
        time.sleep(cleanup_interval)


def _cleanup_expired_events() -> None:
    """Remove expired events from buffer to prevent memory bloat."""
    global config

    # Reload config for hot reload support
    config = _load_config()
    time_window = config.get("pairing", {}).get("time_window_seconds", 30)
    expiry_threshold = time.time() - (time_window * 2)
    expired_items: list[tuple[CameraPair, str, CameraEvent]] = []

    for pair in camera_pairs:
        with pair_locks[pair.id]:
            if pair.front_event and pair.front_event.timestamp_unix < expiry_threshold:
                expired_items.append((pair, pair.front, pair.front_event))
            if pair.rear_event and pair.rear_event.timestamp_unix < expiry_threshold:
                expired_items.append((pair, pair.rear, pair.rear_event))

    for pair, camera_id, event in expired_items:
        pair_id = pair.id
        with pair_locks[pair_id]:
            is_front = camera_id == pair.front
            current_event = pair.front_event if is_front else pair.rear_event

            if not current_event or current_event.timestamp_unix >= expiry_threshold:
                continue

            age = time.time() - current_event.timestamp_unix
            missing_camera = pair.rear if is_front else pair.front

            if is_front:
                pair.front_event = None
            else:
                pair.rear_event = None

        logging.warning(
            f"Unpaired event expired from {camera_id} after {age:.1f}s - "
            f"{missing_camera} may be offline, processing single camera event"
        )

        visit_id = _process_camera_pair(pair)

        # Alert #4: Possible Offline Camera Alert
        if visit_id:
            _send_alert(
                alert_type="camera_offline",
                visit_id=visit_id,
                plate=None,
                camera_id=missing_camera,
                message=f"Camera {missing_camera} may be offline - no events received within {time_window}s window",
                event_data=event,
            )

    if expired_items:
        logging.warning(f"Cleaned up {len(expired_items)} expired events from buffer")


def _get_camera_pair(camera_id: str) -> CameraPair | None:
    """Find the camera pair configuration for a given camera ID."""
    return next(
        (
            pair
            for pair in camera_pairs
            if pair.front == camera_id or pair.rear == camera_id
        ),
        None,
    )


def _extract_plate(result: dict[str, Any]) -> str | None:
    """Extract license plate from result. Stream sends plate as a simple string."""
    plate = result.get("plate")

    if not plate or not isinstance(plate, str):
        logging.error(f"Invalid plate data: {plate} (type: {type(plate).__name__})")
        return None

    return plate.strip().upper()


def _extract_best_make_model(results: list[dict[str, Any]]) -> tuple[str | None, float]:
    """
    Extract the best (highest confidence) make/model from results.
    Returns combined "MAKE MODEL" string.

    Returns:
        Tuple of (make_model, score)
    """
    best_make_model = None
    best_score = 0.0

    for result in results:
        model_make_list = result.get("model_make", [])

        for mm in model_make_list:
            make = mm.get("make", "").strip().upper()
            model = mm.get("model", "").strip().upper()
            score = mm.get("score", 0.0)

            if (make or model) and score > best_score:
                best_make_model = f"{make} {model}".strip()
                best_score = score

    return best_make_model, best_score


def _check_plate_in_vehicles_db(
    plate: str | None,
) -> tuple[bool, dict[str, str] | None]:
    """
    Check if plate exists in Front-Rear database.

    Returns:
        Tuple of (found, vehicle_info)
    """
    if not plate:
        return False, None

    vehicle_info = csv_vehicles.get(plate.upper())
    return vehicle_info is not None, vehicle_info


async def _send_alert_async(
    alert_type: str,
    visit_id: int,
    plate: str | None = None,
    camera_id: str | None = None,
    message: str | None = None,
    event_data: CameraEvent | None = None,
    detected_make_model: str | None = None,
    make_model_score: float | None = None,
) -> None:
    """Send alert to ParkPow using the trigger-alert endpoint (async).

    Args:
        alert_type: Type of alert (plate_mismatch, no_rear_plate, etc.)
        visit_id: Visit ID from ParkPow
        plate: License plate (optional, for logging)
        camera_id: Camera ID (optional, for logging)
        message: Alert message (optional, for logging)
        event_data: Event data (optional, for logging)
        detected_make_model: Detected vehicle make/model (optional, for logging)
        make_model_score: Confidence score (optional, for logging)
    """
    # Reload config for hot reload support
    current_config = _load_config()
    alert_config = current_config.get("alerts", {}).get(alert_type, {})
    if not alert_config.get("enabled", True):
        logging.info(f"Alert {alert_type} is disabled, skipping")
        return

    alert_template_id = alert_config.get("alert_template_id")
    if not alert_template_id:
        logging.error(
            f"Alert template ID not configured for {alert_type}, skipping alert"
        )
        return

    parkpow_config = current_config.get("parkpow", {})
    alert_endpoint = parkpow_config["alert_endpoint"]
    token = parkpow_config["token"]

    payload = {"visit_id": visit_id, "alert_template_id": alert_template_id}

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    if _aiohttp_session is None:
        logging.error("Aiohttp session not initialized")
        return

    try:
        async with _aiohttp_session.post(
            alert_endpoint,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            response.raise_for_status()
            response_data = await response.json()
            alert_id = response_data.get("alert_id")

            logging.info(
                f"Alert {alert_type} created (alert_id={alert_id}) for visit {visit_id}: {message}"
            )

    except Exception as e:
        logging.error(f"Failed to send alert {alert_type} for visit {visit_id}: {e}")


def _send_alert(
    alert_type: str,
    visit_id: int,
    plate: str | None = None,
    camera_id: str | None = None,
    message: str | None = None,
    event_data: CameraEvent | None = None,
    detected_make_model: str | None = None,
    make_model_score: float | None = None,
) -> None:
    """Send alert to ParkPow using the trigger-alert endpoint (non-blocking).

    This function schedules the alert to be sent asynchronously and returns immediately.

    Args:
        alert_type: Type of alert (plate_mismatch, no_rear_plate, etc.)
        visit_id: Visit ID from ParkPow
        plate: License plate (optional, for logging)
        camera_id: Camera ID (optional, for logging)
        message: Alert message (optional, for logging)
        event_data: Event data (optional, for logging)
        detected_make_model: Detected vehicle make/model (optional, for logging)
        make_model_score: Confidence score (optional, for logging)
    """
    if _loop is None or _aiohttp_session is None:
        logging.error("Asyncio event loop not initialized, cannot send alert")
        return

    # Schedule the async task without waiting for it
    asyncio.run_coroutine_threadsafe(
        _send_alert_async(
            alert_type,
            visit_id,
            plate,
            camera_id,
            message,
            event_data,
            detected_make_model,
            make_model_score,
        ),
        _loop,
    )


async def _forward_to_parkpow_async(event: CameraEvent) -> int | None:
    """Forward camera data to ParkPow webhook URL (async).

    Returns:
        visit_id if successful, None otherwise
    """
    # Reload config for hot reload support
    current_config = _load_config()
    parkpow_config = current_config.get("parkpow", {})
    webhook_url = parkpow_config["webhook_endpoint"]
    token = parkpow_config["token"]

    json_data = event.original_json_data
    all_files = event.original_files

    headers = {"Authorization": f"Token {token}"}

    if _aiohttp_session is None:
        logging.error("Aiohttp session not initialized")
        return None

    try:
        if all_files:
            # Create FormData for multipart upload
            data = aiohttp.FormData()
            data.add_field("json", json.dumps(json_data))

            for file_name, file_content in all_files.items():
                data.add_field(
                    file_name,
                    file_content,
                    filename=file_name,
                    content_type="application/octet-stream",
                )

            async with _aiohttp_session.post(
                webhook_url,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
        else:
            async with _aiohttp_session.post(
                webhook_url,
                json=json_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                response.raise_for_status()
                response_data = await response.json()

        visit_id = response_data[0].get("id") if response_data else None

        if visit_id:
            logging.info(f"Created visit {visit_id} in ParkPow")
            return visit_id
        else:
            logging.warning(f"ParkPow response missing visit id: {response_data}")
            return None

    except Exception as e:
        logging.error(f"Failed to forward to ParkPow: {e}")
        return None


def _forward_to_parkpow(event: CameraEvent) -> int | None:
    """Forward camera data to ParkPow webhook URL (blocking wrapper).

    This function is intentionally blocking because we need the visit_id
    immediately to create alerts.

    Returns:
        visit_id if successful, None otherwise
    """
    if _loop is None or _aiohttp_session is None:
        logging.error("Asyncio event loop not initialized, cannot forward to ParkPow")
        return None

    # Run the async function and wait for the result
    future = asyncio.run_coroutine_threadsafe(_forward_to_parkpow_async(event), _loop)
    try:
        return future.result(timeout=15)
    except Exception as e:
        logging.error(f"Failed to forward to ParkPow: {e}")
        return None


def _process_camera_pair(pair: CameraPair) -> int | None:
    """
    Process matched front/rear camera pair and trigger alerts if needed.

    Implements all three alert conditions:
    - Alert #1: Plate not in Front-Rear DB
    - Alert #2: Missing rear plate (only if camera not offline)
    - Alert #3: Make/model mismatch with confidence thresholds

    Args:
        pair: Camera pair with events to process

    Returns:
        visit_id if successfully forwarded to ParkPow, None otherwise
    """
    front_event = pair.front_event
    rear_event = pair.rear_event

    front_plate = None
    rear_plate = None

    if front_event and front_event.results:
        front_plate = _extract_plate(front_event.results[0])

    if rear_event and rear_event.results:
        rear_plate = _extract_plate(rear_event.results[0])

    all_results = []
    if front_event and front_event.results:
        all_results.extend(front_event.results)
    if rear_event and rear_event.results:
        all_results.extend(rear_event.results)

    detected_make_model, make_model_score = (
        _extract_best_make_model(all_results) if all_results else (None, 0.0)
    )

    # Forward data to ParkPow first to create visit
    data_to_forward = rear_event if rear_event else front_event
    if not data_to_forward:
        logging.warning(f"No event data to forward for pair {pair.front}/{pair.rear}")
        return None

    visit_id = _forward_to_parkpow(data_to_forward)
    if not visit_id:
        logging.error(
            f"Failed to create visit in ParkPow for pair {pair.front}/{pair.rear}, skipping alerts"
        )
        return None

    # Alert #2: No Rear Plate Alert (only if rear camera not offline)
    if not rear_plate and rear_event:
        logging.warning(
            f"No rear plate detected for camera pair {pair.front}/{pair.rear}"
        )
        _send_alert(
            alert_type="no_rear_plate",
            visit_id=visit_id,
            plate=front_plate,
            camera_id=pair.rear,
            message=f"No rear plate detected for front plate {front_plate}",
            event_data=rear_event,
        )

        if not front_plate:
            return None

    # Alert #1: Plate Mismatch Alert (either camera plate not in Front-Rear DB)
    front_in_db, front_vehicle_info = _check_plate_in_vehicles_db(front_plate)
    rear_in_db, rear_vehicle_info = _check_plate_in_vehicles_db(rear_plate)

    if front_plate and not front_in_db:
        logging.warning(f"Front plate {front_plate} not found in Front-Rear database")
        _send_alert(
            alert_type="plate_mismatch",
            visit_id=visit_id,
            plate=front_plate,
            camera_id=pair.front,
            message=f"License plate {front_plate} not found in Front-Rear Vehicle Database",
            event_data=front_event,
            detected_make_model=detected_make_model,
            make_model_score=make_model_score,
        )

    if rear_plate and not rear_in_db:
        logging.warning(f"Rear plate {rear_plate} not found in Front-Rear database")
        _send_alert(
            alert_type="plate_mismatch",
            visit_id=visit_id,
            plate=rear_plate,
            camera_id=pair.rear,
            message=f"License plate {rear_plate} not found in Front-Rear Vehicle Database",
            event_data=rear_event,
            detected_make_model=detected_make_model,
            make_model_score=make_model_score,
        )

    # Alert #3: Make/Model Mismatch Alert
    # Reload config for hot reload support
    current_config = _load_config()
    make_model_threshold = current_config.get("thresholds", {}).get(
        "make_model_confidence", 0.2
    )
    reference_plate = (
        rear_plate if rear_in_db else (front_plate if front_in_db else None)
    )
    reference_vehicle_info = rear_vehicle_info if rear_in_db else front_vehicle_info

    if reference_plate and reference_vehicle_info:
        front_rear_make = reference_vehicle_info.get("make", "")
        front_rear_model = reference_vehicle_info.get("model", "")
        front_rear_make_model = f"{front_rear_make} {front_rear_model}".strip()
        make_model_mismatch = (
            detected_make_model and detected_make_model != front_rear_make_model
        )

        if make_model_mismatch and make_model_score >= make_model_threshold:
            logging.warning(
                f"Make/model mismatch for {reference_plate}: "
                f"Detected: {detected_make_model} (score: {make_model_score:.2f}), "
                f"Front-Rear DB: {front_rear_make_model}"
            )
            _send_alert(
                alert_type="make_model_mismatch",
                visit_id=visit_id,
                plate=reference_plate,
                camera_id=pair.rear if rear_plate else pair.front,
                message=(
                    f"Vehicle make/model mismatch for {reference_plate}: "
                    f"Detected {detected_make_model} (confidence: {make_model_score:.2f}), "
                    f"Expected {front_rear_make_model} from Front-Rear database"
                ),
                event_data=rear_event if rear_event else front_event,
                detected_make_model=detected_make_model,
                make_model_score=make_model_score,
            )

    return visit_id


def _authenticate_request(json_data: dict[str, Any]) -> tuple[str, int] | None:
    """
    Authenticate incoming webhook request.

    Returns:
        None if authentication succeeds, or (error_message, status_code) tuple if it fails.
    """
    expected_token = os.getenv("STREAM_API_TOKEN")
    if not expected_token:
        logging.error(
            "STREAM_API_TOKEN not configured - rejecting request for security"
        )
        return "Unauthorized: Authentication not configured", 401

    auth_header = get_header("Authorization", json_data)
    if not auth_header:
        logging.error("Missing Authorization header in request from Stream")
        return "Unauthorized: Missing Authorization header", 401

    token = auth_header.split()[-1]

    if not token or token.lower() in ("token", "bearer"):
        logging.error("Invalid or missing token in Authorization header")
        return "Unauthorized: Malformed Authorization header", 401

    if token != expected_token:
        logging.error("Invalid STREAM_API_TOKEN in Authorization header")
        return "Forbidden: Invalid token", 403

    return None


def process_request(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
) -> tuple[str, int]:
    auth_error = _authenticate_request(json_data)
    if auth_error:
        return auth_error

    data = json_data.get("data", {})
    camera_id = data.get("camera_id")
    results = data.get("results", [])
    timestamp_str = data.get("timestamp", "")
    pair = _get_camera_pair(camera_id)

    if not pair:
        logging.warning(f"Camera {camera_id} is not configured in any pair")
        return "Camera not configured in any pair", 200

    try:
        if "T" in timestamp_str and timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(timestamp_str)
        else:
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        timestamp_unix = dt.timestamp()
    except (ValueError, AttributeError) as e:
        logging.warning(
            f"Failed to parse timestamp '{timestamp_str}': {e}, using current time"
        )
        timestamp_unix = time.time()

    event = CameraEvent(
        camera_id=camera_id,
        results=results,
        timestamp=timestamp_str,
        timestamp_local=data.get("timestamp_local"),
        timestamp_unix=timestamp_unix,
        original_json_data=json_data,
        original_files=all_files,
    )

    pair_id = pair.id
    is_front = camera_id == pair.front

    old_front_event = None
    old_rear_event = None
    should_send_overwrite_alert = False
    missing_camera_id: str | None = None
    overwrite_age: float | None = None
    overwrite_old_event: CameraEvent | None = None

    with pair_locks[pair_id]:
        old_event = pair.front_event if is_front else pair.rear_event

        if old_event:
            old_timestamp = old_event.timestamp_unix
            age = time.time() - old_timestamp
            missing_camera = pair.rear if is_front else pair.front

            old_plate = (
                _extract_plate(old_event.results[0]) if old_event.results else None
            )
            new_plate = _extract_plate(results[0]) if results else None

            if old_plate != new_plate:
                logging.warning(
                    f"Overwriting unpaired event from {camera_id} (age: {age:.1f}s, old plate: {old_plate}) - "
                    f"new vehicle ({new_plate}) detected before pair completed, {missing_camera} may be offline"
                )

                old_front_event = old_event if is_front else None
                old_rear_event = old_event if not is_front else None
                should_send_overwrite_alert = True
                missing_camera_id = missing_camera
                overwrite_age = age
                overwrite_old_event = old_event
            else:
                logging.debug(
                    f"Updating event for {camera_id} with same plate {new_plate} (age: {age:.1f}s)"
                )

        if is_front:
            pair.front_event = event
        else:
            pair.rear_event = event

    if should_send_overwrite_alert and missing_camera_id is not None:
        old_pair_front = pair.front_event
        old_pair_rear = pair.rear_event
        pair.front_event = old_front_event
        pair.rear_event = old_rear_event

        visit_id = _process_camera_pair(pair)

        pair.front_event = old_pair_front
        pair.rear_event = old_pair_rear

        # Alert #4: Possible Offline Camera Alert
        if visit_id:
            _send_alert(
                alert_type="camera_offline",
                visit_id=visit_id,
                plate=None,
                camera_id=missing_camera_id,
                message=f"Camera {missing_camera_id} may be offline - unpaired event overwritten after {overwrite_age:.1f}s",
                event_data=overwrite_old_event,
            )

    should_process_pair = False

    with pair_locks[pair_id]:
        front_event = pair.front_event
        rear_event = pair.rear_event

        # Reload config for hot reload support
        current_config = _load_config()
        time_window = current_config.get("pairing", {}).get("time_window_seconds", 30)
        now = time.time()
        front_valid = front_event and (now - front_event.timestamp_unix) <= time_window
        rear_valid = rear_event and (now - rear_event.timestamp_unix) <= time_window

        if front_valid and rear_valid:
            logging.info(f"Processing camera pair {pair.front}/{pair.rear}")
            should_process_pair = True

    if should_process_pair:
        _process_camera_pair(pair)
        pair.front_event = None
        pair.rear_event = None
        return "Processed camera pair", 200
    else:
        status_msg = []
        if not front_valid:
            status_msg.append(
                f"front camera ({pair.front}) {'missing' if not front_event else 'expired'}"
            )
        if not rear_valid:
            status_msg.append(
                f"rear camera ({pair.rear}) {'missing' if not rear_event else 'expired'}"
            )

        logging.info(
            f"Event buffered for {camera_id}, waiting for: {', '.join(status_msg)}"
        )
        return "Event buffered, waiting for pair", 200
