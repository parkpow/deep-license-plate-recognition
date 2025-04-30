import csv
import logging
import time
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

_config_cache: list[dict[str, Any]] = []
_last_load: float = 0.0


def _load_config() -> list[dict[str, Any]]:
    try:
        with open("dot_config.csv", newline="") as f:
            reader = csv.DictReader(f)
            rows: list[dict[str, Any]] = []
            for row in reader:
                try:
                    cam = row["CameraID"].strip()
                    s = int(row["StartDOT"].strip())
                    e = int(row["EndDOT"].strip())
                    dest = row["Destination"].strip()
                except (KeyError, ValueError) as ex:
                    logging.warning(f"Skipping invalid row {row}: {ex}")
                    continue
                rows.append(
                    {"CameraID": cam, "StartDOT": s, "EndDOT": e, "Destination": dest}
                )
            logging.info(f"Loaded {len(rows)} camera configs")
            return rows
    except Exception as ex:
        logging.error(f"Error loading config: {ex}")
        return []


def _get_config() -> list[dict[str, Any]]:
    global _config_cache, _last_load
    now = time.time()
    if now - _last_load > 60 * 30:
        _config_cache = _load_config()
        _last_load = now
    return _config_cache


def process_request(
    json_data: dict[str, Any], upload_file: bytes | None = None
) -> tuple[str, int]:
    data = json_data.get("data", {})
    camera_id = data.get("camera_id") or data.get("CameraID")
    results = data.get("results", [])

    if not results:
        logging.info(f"No results found for camera {camera_id}, dropping.")
        return "Dropped", 200

    entry = next((e for e in _get_config() if e["CameraID"] == camera_id), None)
    if not entry:
        logging.info(f"No config for camera {camera_id}, dropping.")
        return "Dropped", 200

    valid_results = _filter_results_by_direction(results, entry, camera_id)

    if not valid_results:
        logging.info(f"All results for camera {camera_id} are out of range, dropping.")
        return "Dropped", 200

    json_data["results"] = valid_results

    return _forward_to_destination(json_data, entry["Destination"])


def _filter_results_by_direction(
    results: list[dict[str, Any]], entry: dict[str, Any], camera_id: str
) -> list[dict[str, Any]]:
    s, e = entry["StartDOT"], entry["EndDOT"]
    valid_results = []

    for result in results:
        direction = result.get("direction")
        if direction is None:
            logging.warning(f"No direction found in result for camera {camera_id}")
            continue
        try:
            direction = int(direction)
        except (TypeError, ValueError):
            logging.warning(
                f"Invalid direction {direction} in result for camera {camera_id}"
            )
            continue

        in_range = (
            (s <= direction <= e) if s <= e else (direction >= s or direction <= e)
        )
        if in_range:
            valid_results.append(result)
        else:
            logging.info(
                f"Result with direction {direction} out of range {s}–{e} for camera {camera_id}, dropping."
            )

    return valid_results


def _forward_to_destination(
    json_data: dict[str, Any], destination: str
) -> tuple[str, int]:
    try:
        resp = requests.post(destination, json=json_data, timeout=5)
        resp.raise_for_status()
        logging.info(f"Forwarded to {destination}")
        return "Forwarded", 200
    except requests.RequestException as ex:
        logging.error(f"Failed to forward to {destination}: {ex}")
        return "Failed to forward", 503
