import logging
import time
from datetime import datetime
from typing import Any


def parse_timestamp(timestamp_str: str) -> float:
    """Parse timestamp string to unix timestamp. Returns current time if parsing fails."""
    try:
        if "T" in timestamp_str and timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(timestamp_str)
        else:
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        return dt.timestamp()
    except (ValueError, AttributeError) as e:
        logging.warning(
            f"Failed to parse timestamp '{timestamp_str}': {e}, using current time"
        )
        return time.time()


def shorten_id(camera_id: str | None) -> str:
    """Helper to shorten camera ID for logging."""
    if not camera_id:
        return ""
    return f"...{camera_id[-12:]}" if len(camera_id) >= 60 else camera_id


def extract_plate(result: dict[str, Any]) -> str | None:
    """Extract license plate from result. Stream sends plate as a simple string."""
    plate = result.get("plate")

    if not plate or not isinstance(plate, str):
        logging.error(f"Invalid plate data: {plate} (type: {type(plate).__name__})")
        return None

    return plate.strip().upper()


def extract_best_make_model(results: list[dict[str, Any]]) -> tuple[str | None, float]:
    """Extract highest confidence make/model as "MAKE MODEL" string and score."""
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


def stream_response(
    message: str, status: int, camera_id: str | None = None
) -> tuple[str, int]:
    """Log exactly what is returned to Stream and return it."""
    cam = f" for {shorten_id(camera_id)}" if camera_id else ""
    log = f"Returned {status} {message!r}{cam}"
    if status >= 500:
        logging.error(log)
    elif status >= 400:
        logging.warning(log)
    else:
        logging.info(log)
    return message, status


def check_plate_in_vehicles_db(
    plate: str | None, csv_db: dict[str, dict[str, str]]
) -> tuple[bool, dict[str, str] | None]:
    """Check if plate exists in database. Returns (found, vehicle_info)."""
    if not plate:
        return False, None

    vehicle_info = csv_db.get(plate.upper())
    return vehicle_info is not None, vehicle_info
