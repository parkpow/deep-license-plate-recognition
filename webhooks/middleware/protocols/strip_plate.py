import json
import logging
import os
from datetime import datetime
from copy import deepcopy
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def strip_data_in_jsonl_file(
    jsonl_file: str,
    plate: str,
    converted_payload: dict[str, Any],
    camera_id: str,
    timestamp: str,
) -> None:
    """Strip the plate from the JSONL file."""

    if not os.path.exists(jsonl_file):
        logging.error(f"JSONL file {jsonl_file} does not exist.")
        return

    try:
        with open(jsonl_file, "r") as file:
            lines = file.readlines()

        updated_lines = []
        for line in lines:
            data = json.loads(line)
            try:
                if data["results"][0]["plate"] == plate:
                    logging.info(
                        f"Camera: {camera_id} - Stripping data in local file for prediction at {timestamp}"
                    )
                    data["results"] = converted_payload["data"]["results"]
            except (KeyError, IndexError):
                # Line doesn't match expected format, keep it as is.
                pass
            updated_lines.append(json.dumps(data) + "\n")

        with open(jsonl_file, "w") as file:
            file.writelines(updated_lines)
    except (IOError, json.JSONDecodeError) as e:
        logging.error(
            f"Error stripping data in local file for prediction at {timestamp} from {jsonl_file}: {e}"
        )


def convert_plate_format_to_vehicle_format(original):

    new_payload = {
        "hook": deepcopy(original["hook"]),
        "data": {
            "camera_id": original["data"]["camera_id"],
            "filename": original["data"]["filename"],
            "timestamp": original["data"]["timestamp"],
            "timestamp_local": original["data"]["timestamp_local"],
            "timestamp_camera": original["data"].get("timestamp_camera"),
            "results": [],
        },
    }

    for result in original["data"]["results"]:
        vehicle = {
            "type": result.get("vehicle", {}).get("type", "Unknown"),
            "score": result.get("vehicle", {}).get("score", 0),
            "box": result.get("vehicle", {}).get("box", {}),
        }

        props = {"make_model": [], "orientation": [], "color": []}

        for mm in result.get("model_make", []):
            props["make_model"].append(
                {"make": "generic", "model": "Unknown", "score": mm.get("score", 0)}
            )

        for o in result.get("orientation", []):
            props["orientation"].append(
                {"value": o.get("orientation", "Unknown"), "score": o.get("score", 0)}
            )

        for c in result.get("color", []):
            props["color"].append({"value": "Unknown", "score": c.get("score", 0)})

        new_result = {
            "source_url": result.get("source_url"),
            "position_sec": float(result.get("position_sec", 0)),
            "direction": result.get("direction"),
            "speed": result.get("speed"),
            "speed_score": result.get("speed_score"),
            "vehicle": {
                "type": "generic",
                "score": vehicle["score"],
                "box": vehicle["box"],
                "props": props,
            },
            "plate": None,
            "user_data": result.get("user_data", ""),
        }

        new_payload["data"]["results"].append(new_result)

    return new_payload


def process_request(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
) -> tuple[str, int]:

    if not all_files:
        logging.error("No files uploaded.")
        return "No files uploaded.", 400

    upload_file = all_files.get("upload")

    if not upload_file:
        logging.error(f"No file uploaded for {json_data}")
        return "No file uploaded.", 400

    prediction_data = json_data.get("data")
    if not isinstance(prediction_data, dict):
        logging.error(f"Missing or invalid 'data' field in JSON: {json.dumps(json_data)}")
        return "Invalid data format.", 400
    
    timestamp = prediction_data["timestamp"]
    camera_id = prediction_data["camera_id"]

    try:
        plate = prediction_data["results"][0]["plate"]
    except (KeyError, IndexError, TypeError):
        plate = None

    if not all((timestamp, camera_id, plate)):
        logging.error(f"Missing required fields in prediction data: {json.dumps(json_data)}")
        return "Invalid prediction data format.", 400

    try:
        event_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        filename = event_dt.strftime("%y-%m-%d.jsonl")
    except Exception as e:
        logging.error(f"Invalid timestamp format: {timestamp} ({e})")
        return "Invalid timestamp format.", 400

    converted_payload = convert_plate_format_to_vehicle_format(json_data)

    data = {"json": json.dumps(converted_payload)}

    headers = {}
    if os.getenv("PARKPOW_TOKEN"):
        headers = {"Authorization": f'Token {os.getenv("PARKPOW_TOKEN")}'}

    try:
        response = requests.post(
            os.getenv("WEBHOOK_URL"), data=data, files=all_files, headers=headers
        )
        response.raise_for_status()
        logging.info(
            f"Camera: {camera_id} - Vehicle activity at {timestamp}. Request was successful."
        )
    except requests.exceptions.RequestException as err:
        logging.error(
            f"Camera: {camera_id} - Vehicle activity at {timestamp}. Error processing the request: {err}"
        )
        return f"Failed to process the request: {err}", 500

    try:
        strip_data_in_jsonl_file(
            os.path.join("/user-data", f"{camera_id}_{filename}"),
            plate,
            converted_payload,
            camera_id,
            timestamp,
        )
    except Exception as e:
        logging.error(
            f"Error processing JSONL file for camera {camera_id} at {timestamp}: {e}"
        )
        return f"Failed to process JSONL file: {e}", 500

    return "Request was successful", response.status_code
