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

import csv
import json
import logging
import os
import threading
import time
from datetime import UTC, datetime
from io import BytesIO
from threading import Lock
from typing import Any

import requests

from protocols.shared.utils import get_header, replace_env_vars

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

front_rear_vehicles: dict[str, dict[str, str]] = {}  # plate -> {make, model}
camera_pairs: list[dict[str, str]] = []  # List of {front, rear, description}
config: dict[str, Any] = {}
event_buffer: dict[str, dict[str, Any]] = {}  # camera_id -> latest event
buffer_lock = Lock()

_config_cache: dict[str, Any] | None = None
_config_last_load: float = 0.0


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

        config_data = replace_env_vars(config_data)
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


def load_front_rear_csv() -> None:
    """Load Front-Rear Vehicle Database CSV into memory for fast lookups."""
    global front_rear_vehicles, config

    config = _load_config()
    csv_path = config.get("front_rear_csv_path", "front_rear.csv")

    try:
        front_rear_vehicles.clear()
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
                front_rear_vehicles[plate] = occurrences[0]
            else:
                duplicates += len(occurrences)

        if not front_rear_vehicles:
            logging.error(f"Front-Rear CSV file is empty: {csv_path}")
            raise ValueError(
                "Front-Rear database is empty, cannot operate without vehicle data"
            )

        logging.info(
            f"Loaded {len(front_rear_vehicles)} vehicles from Front-Rear database "
            f"({total_rows} rows, {duplicates} duplicates skipped, {skipped} invalid plates skipped)"
        )

    except FileNotFoundError:
        logging.error(f"Front-Rear CSV file not found: {csv_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading Front-Rear CSV: {e}")
        raise


def initialize_front_rear_middleware() -> None:
    """
    Initialize Front-Rear middleware at startup.

    Loads:
    - Front-Rear Vehicle Database (CSV)
    - Configuration (camera pairs, thresholds, endpoints)
    - Schedules periodic cleanup of expired buffered events
    """
    global camera_pairs, config

    load_front_rear_csv()
    config = _load_config()
    camera_pairs = config.get("camera_pairs", [])
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

    logging.info(
        f"Initialized Front-Rear middleware with {len(camera_pairs)} camera pairs"
    )

    cleanup_thread = threading.Thread(target=_cleanup_task_loop, daemon=True)
    cleanup_thread.start()


def _cleanup_task_loop() -> None:
    """Daemon thread that periodically runs cleanup of expired events."""
    cleanup_interval = config.get("pairing", {}).get("cleanup_interval_seconds", 60)
    while True:
        try:
            _cleanup_expired_events()
        except Exception as e:
            logging.error(f"Error in cleanup task: {e}")
        time.sleep(cleanup_interval)


def _cleanup_expired_events() -> None:
    """Remove expired events from buffer to prevent memory bloat."""
    global event_buffer, config

    time_window = config.get("pairing", {}).get("time_window_seconds", 30)
    expiry_threshold = time.time() - (time_window * 2)

    with buffer_lock:
        expired_cameras = [
            camera_id
            for camera_id, event in event_buffer.items()
            if event.get("timestamp_unix", 0) < expiry_threshold
        ]

        for camera_id in expired_cameras:
            event = event_buffer[camera_id]
            age = time.time() - event.get("timestamp_unix", 0)
            pair = _get_camera_pair(camera_id)
            if pair:
                missing_camera = (
                    pair["rear"] if camera_id == pair["front"] else pair["front"]
                )

                logging.warning(
                    f"Unpaired event expired from {camera_id} after {age:.1f}s - "
                    f"{missing_camera} may be offline, processing single camera event"
                )

                front_event = event if camera_id == pair["front"] else None
                rear_event = event if camera_id == pair["rear"] else None
                _process_camera_pair(
                    front_event, rear_event, pair, camera_offline=missing_camera
                )

                # Alert #4: Possible Offline Camera Alert
                _send_alert(
                    alert_type="camera_offline",
                    plate=None,
                    camera_id=missing_camera,
                    message=f"Camera {missing_camera} may be offline - no events received within {time_window}s window",
                    event_data=event,
                )

            del event_buffer[camera_id]

        if expired_cameras:
            logging.warning(
                f"Cleaned up {len(expired_cameras)} expired events from buffer"
            )


def _get_camera_pair(camera_id: str) -> dict[str, str] | None:
    """Find the camera pair configuration for a given camera ID."""
    return next(
        (
            pair
            for pair in camera_pairs
            if pair.get("front") == camera_id or pair.get("rear") == camera_id
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


def _check_plate_in_front_rear_db(
    plate: str | None,
) -> tuple[bool, dict[str, str] | None]:
    """
    Check if plate exists in Front-Rear database.

    Returns:
        Tuple of (found, vehicle_info)
    """
    if not plate:
        return False, None

    vehicle_info = front_rear_vehicles.get(plate.upper())
    return vehicle_info is not None, vehicle_info


def _send_alert(
    alert_type: str,
    plate: str | None,
    camera_id: str,
    message: str,
    event_data: dict[str, Any] | None = None,
    detected_make_model: str | None = None,
    make_model_score: float = 0.0,
) -> None:
    alert_config = config.get("alerts", {}).get(alert_type, {})
    if not alert_config.get("enabled", True):
        logging.info(f"Alert {alert_type} is disabled, skipping")
        return

    parkpow_config = config.get("parkpow", {})
    alert_endpoint = parkpow_config["alert_endpoint"]
    token = parkpow_config["token"]

    alert_name = alert_config.get("name", alert_type)

    payload = {
        "alert_type": alert_type,
        "alert_name": alert_name,
        "license_plate": plate,
        "camera_id": camera_id,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }

    if detected_make_model:
        payload["detected_vehicle"] = {
            "make_model": detected_make_model,
            "score": make_model_score,
        }

    if event_data:
        payload["event_data"] = {
            "timestamp": event_data.get("timestamp"),
            "timestamp_local": event_data.get("timestamp_local"),
        }

    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

    try:
        response = requests.post(
            alert_endpoint, json=payload, headers=headers, timeout=10
        )
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send alert {alert_type}: {e}")


def _forward_to_parkpow(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None
) -> None:
    """Forward rear camera data to ParkPow webhook URL."""
    parkpow_config = config.get("parkpow", {})
    webhook_url = parkpow_config["webhook_endpoint"]
    token = parkpow_config["token"]

    headers = {"Authorization": f"Token {token}"}

    try:
        if all_files:
            files_to_send = {}
            for file_name, file_content in all_files.items():
                files_to_send[file_name] = (file_name, BytesIO(file_content))

            data = {"json": json.dumps(json_data)}
            response = requests.post(
                webhook_url, data=data, files=files_to_send, headers=headers, timeout=10
            )
        else:
            response = requests.post(
                webhook_url, json=json_data, headers=headers, timeout=10
            )

        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to forward to ParkPow: {e}")


def _process_camera_pair(
    front_event: dict[str, Any] | None,
    rear_event: dict[str, Any] | None,
    pair: dict[str, str],
    camera_offline: str | None = None,
) -> None:
    """
    Process matched front/rear camera pair and trigger alerts if needed.

    Implements all three alert conditions:
    - Alert #1: Plate not in Front-Rear DB
    - Alert #2: Missing rear plate (only if camera not offline)
    - Alert #3: Make/model mismatch with confidence thresholds

    Args:
        front_event: Front camera event data or None
        rear_event: Rear camera event data or None
        pair: Camera pair configuration
        camera_offline: Camera ID that is offline (if applicable), to skip redundant alerts
    """

    front_plate = None
    rear_plate = None

    if front_event and front_event.get("results"):
        front_plate = _extract_plate(front_event["results"][0])

    if rear_event and rear_event.get("results"):
        rear_plate = _extract_plate(rear_event["results"][0])

    all_results = []
    if front_event and front_event.get("results"):
        all_results.extend(front_event["results"])
    if rear_event and rear_event.get("results"):
        all_results.extend(rear_event["results"])

    detected_make_model, make_model_score = (
        _extract_best_make_model(all_results) if all_results else (None, 0.0)
    )

    # Alert #2: No Rear Plate Alert (only if rear camera not offline)
    if not rear_plate and camera_offline != pair["rear"]:
        logging.warning(
            f"No rear plate detected for camera pair {pair['front']}/{pair['rear']}"
        )
        _send_alert(
            alert_type="no_rear_plate",
            plate=None,
            camera_id=pair["rear"],
            message="License plate not detected on rear camera",
            event_data=rear_event if rear_event else None,
            detected_make_model=detected_make_model,
            make_model_score=make_model_score,
        )
        if not front_plate:
            return

    # Alert #1: Plate Mismatch Alert (either camera plate not in Front-Rear DB)
    front_in_db, front_vehicle_info = _check_plate_in_front_rear_db(front_plate)
    rear_in_db, rear_vehicle_info = _check_plate_in_front_rear_db(rear_plate)

    if front_plate and not front_in_db:
        logging.warning(f"Front plate {front_plate} not found in Front-Rear database")
        _send_alert(
            alert_type="plate_mismatch",
            plate=front_plate,
            camera_id=pair["front"],
            message=f"License plate {front_plate} not found in Front-Rear Vehicle Database",
            event_data=front_event if front_event else None,
            detected_make_model=detected_make_model,
            make_model_score=make_model_score,
        )

    if rear_plate and not rear_in_db:
        logging.warning(f"Rear plate {rear_plate} not found in Front-Rear database")
        _send_alert(
            alert_type="plate_mismatch",
            plate=rear_plate,
            camera_id=pair["rear"],
            message=f"License plate {rear_plate} not found in Front-Rear Vehicle Database",
            event_data=rear_event if rear_event else None,
            detected_make_model=detected_make_model,
            make_model_score=make_model_score,
        )

    # Alert #3: Make/Model Mismatch Alert
    make_model_threshold = config.get("thresholds", {}).get(
        "make_model_confidence", 0.7
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
                plate=reference_plate,
                camera_id=pair["rear"] if rear_plate else pair["front"],
                message=(
                    f"Vehicle make/model mismatch for {reference_plate}: "
                    f"Detected {detected_make_model} (confidence: {make_model_score:.2f}), "
                    f"Expected {front_rear_make_model} from Front-Rear database"
                ),
                event_data=rear_event if rear_event else front_event,
                detected_make_model=detected_make_model,
                make_model_score=make_model_score,
            )

    # Forward camera data to ParkPow (prefer rear, fallback to front)
    if rear_event:
        rear_json = rear_event.get("original_json_data")
        rear_files = rear_event.get("original_files")
        if rear_json:
            logging.info(
                f"Forwarding rear camera data for pair {pair['front']}/{pair['rear']}"
            )
            _forward_to_parkpow(rear_json, rear_files)
    elif front_event:
        front_json = front_event.get("original_json_data")
        front_files = front_event.get("original_files")
        if front_json:
            logging.info(
                f"Forwarding front camera data for pair {pair['front']}/{pair['rear']} (rear unavailable)"
            )
            _forward_to_parkpow(front_json, front_files)
    else:
        logging.warning(
            f"No event data to forward for pair {pair['front']}/{pair['rear']}"
        )


def process_request(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
) -> tuple[str, int]:
    """
    Main webhook handler for Front-Rear middleware.

    Buffers events by camera and triggers pair processing when both cameras
    in a pair have captured data within the time window.
    """
    global event_buffer

    expected_token = os.getenv("STREAM_API_TOKEN")
    if expected_token:
        auth_header = get_header("Authorization", json_data)

        if not auth_header:
            logging.error("Missing Authorization header in request from Stream")
            return "Unauthorized: Missing Authorization header", 401

        token = auth_header.split()[-1] if " " in auth_header else auth_header
        if token != expected_token:
            logging.error("Invalid STREAM_API_TOKEN in Authorization header")
            return "Forbidden: Invalid token", 403

    else:
        logging.warning("STREAM_API_TOKEN not configured - skipping authentication")

    data = json_data.get("data", {})
    camera_id = data.get("camera_id")

    if not camera_id:
        logging.error("camera_id not found in webhook data")
        logging.error(f"Full JSON structure: {json.dumps(json_data, indent=2)}")
        return "The camera_id is required.", 400

    pair = _get_camera_pair(camera_id)
    if not pair:
        logging.warning(f"Camera {camera_id} is not configured in any pair")
        return "Camera not configured in any pair", 200

    results = data.get("results", [])
    if not results:
        logging.info(f"No results from camera {camera_id}, dropping event")
        return "No results in webhook", 200

    timestamp_str = data.get("timestamp", "")
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

    event_data = {
        "camera_id": camera_id,
        "results": results,
        "timestamp": timestamp_str,
        "timestamp_local": data.get("timestamp_local"),
        "timestamp_unix": timestamp_unix,
        "original_json_data": json_data,
        "original_files": all_files,
    }

    with buffer_lock:
        if camera_id in event_buffer:
            old_event = event_buffer[camera_id]
            old_timestamp = old_event.get("timestamp_unix", 0)
            age = time.time() - old_timestamp
            missing_camera = (
                pair["rear"] if camera_id == pair["front"] else pair["front"]
            )

            logging.warning(
                f"Overwriting unpaired event from {camera_id} (age: {age:.1f}s) - "
                f"new vehicle detected before pair completed, {missing_camera} may be offline"
            )

            old_front_event = old_event if camera_id == pair["front"] else None
            old_rear_event = old_event if camera_id == pair["rear"] else None
            _process_camera_pair(
                old_front_event, old_rear_event, pair, camera_offline=missing_camera
            )

            # Alert #4: Possible Offline Camera Alert
            _send_alert(
                alert_type="camera_offline",
                plate=None,
                camera_id=missing_camera,
                message=f"Camera {missing_camera} may be offline - unpaired event overwritten after {age:.1f}s",
                event_data=old_event,
            )

        event_buffer[camera_id] = event_data
        front_camera_id = pair["front"]
        rear_camera_id = pair["rear"]
        front_event = event_buffer.get(front_camera_id)
        rear_event = event_buffer.get(rear_camera_id)

        time_window = config.get("pairing", {}).get("time_window_seconds", 30)
        now = time.time()
        front_valid = (
            front_event and (now - front_event.get("timestamp_unix", 0)) <= time_window
        )
        rear_valid = (
            rear_event and (now - rear_event.get("timestamp_unix", 0)) <= time_window
        )

        if front_valid and rear_valid:
            logging.info(f"Processing camera pair {front_camera_id}/{rear_camera_id}")
            if front_camera_id in event_buffer:
                del event_buffer[front_camera_id]
            if rear_camera_id in event_buffer:
                del event_buffer[rear_camera_id]

            _process_camera_pair(front_event, rear_event, pair)

            return "Processed camera pair", 200
        else:
            status_msg = []
            if not front_valid:
                status_msg.append(
                    f"front camera ({front_camera_id}) {'missing' if not front_event else 'expired'}"
                )
            if not rear_valid:
                status_msg.append(
                    f"rear camera ({rear_camera_id}) {'missing' if not rear_event else 'expired'}"
                )

            logging.info(
                f"Event buffered for {camera_id}, waiting for: {', '.join(status_msg)}"
            )
            return "Event buffered, waiting for pair", 200
