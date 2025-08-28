import json
import logging
import os
from copy import deepcopy
from datetime import datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
        with open(jsonl_file) as file:
            lines = file.readlines()

        updated_lines = []
        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:  # skip empty lines
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in {jsonl_file} at line {line_num}: {e}")
                continue

            try:
                if data.get("results") and data["results"][0].get("plate") == plate:
                    data["results"] = converted_payload["data"]["results"]
            except (KeyError, IndexError):
                pass  # structure not as expected

            updated_lines.append(json.dumps(data) + "\n")

        with open(jsonl_file, "w") as file:
            file.writelines(updated_lines)

    except OSError as e:
        logging.error(
            f"Error stripping data in local file for prediction at {timestamp} "
            f"from {jsonl_file}: {e}"
        )


def convert_plate_format_to_vehicle_format(original: dict[str, Any]):

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

        props: dict[str, list[dict[str, Any]]] = {
            "make_model": [],
            "orientation": [],
            "color": [],
        }

        for mm in result.get("model_make", []):
            props["make_model"].append(
                {
                    "make": mm.get("make", "Unknown"),
                    "model": mm.get("model", "Unknown"),
                    "score": mm.get("score", 0),
                }
            )

        for o in result.get("orientation", []):
            props["orientation"].append(
                {"value": o.get("orientation", "Unknown"), "score": o.get("score", 0)}
            )

        for c in result.get("color", []):
            props["color"].append(
                {"value": c.get("color", "Unknown"), "score": c.get("score", 0)}
            )

        new_result = {
            "source_url": result.get("source_url"),
            "position_sec": float(result.get("position_sec", 0)),
            "direction": result.get("direction"),
            "speed": result.get("speed"),
            "speed_score": result.get("speed_score"),
            "vehicle": {
                "type": vehicle["type"],
                "score": vehicle["score"],
                "box": vehicle["box"],
                "props": props,
            },
            "plate": None,
            "user_data": result.get("user_data", ""),
        }

        new_payload["data"]["results"].append(new_result)

    return new_payload


def get_jsonl_filename(camera_id: str, timestamp: str) -> str:
    """Generate the JSONL filename based on camera ID and timestamp.
    Args:
        camera_id (str): The ID of the camera.
        timestamp (str): The timestamp in ISO format.

    Returns:
        str: The formatted filename in format $(camera)_%y-%m-%d.jsonl,
             see https://guides.platerecognizer.com/docs/stream/configuration#jsonlines_file

    """
    try:
        event_dt = datetime.fromisoformat(timestamp)
        return f"{camera_id}_{event_dt.strftime('%y-%m-%d')}.jsonl"
    except ValueError as e:
        logging.error(f"Invalid timestamp format: {timestamp} ({e})")
        raise ValueError("Invalid timestamp format") from e


def post_with_retries(
    url: str,
    data: dict,
    files: dict | None = None,
    headers: dict | None = None,
    allowed_methods: list[str] | None = None,
    retries_total: int = 3,
    backoff_factor: float = 1.0,
    status_forcelist: list[int] | None = None,
) -> requests.Response:
    """Send a POST request with retries using requests and urllib3 Retry."""

    session = requests.Session()
    retries = Retry(
        total=retries_total,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    response = session.post(url, data=data, files=files, headers=headers)
    response.raise_for_status()
    return response


def process_request(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
) -> tuple[str, int]:
    """
    Processes a request and strips plate data from a JSONL file.
    Assumes that after validation, camera_id, timestamp, and timestamp_local are str.
    """

    url = os.getenv("WEBHOOK_URL")
    if not url:
        raise ValueError(
            "WEBHOOK_URL environment variable is not set or empty, if the webhook receiver is ParkPow endpoint, make sure to include PARKPOW_TOKEN environment variable too."
        )

    if not all_files:
        logging.error("No files uploaded.")
        return "No files uploaded.", 400

    upload_file = all_files.get("upload")

    if not upload_file:
        logging.error(f"No file uploaded for {json_data}")
        return "No file uploaded.", 400

    prediction_data = json_data.get("data")
    if not isinstance(prediction_data, dict):
        logging.error(
            f"Missing or invalid 'data' field in JSON: {json.dumps(json_data)}"
        )
        return "Invalid data format.", 400

    timestamp: str | None = prediction_data.get("timestamp")
    timestamp_local: str | None = prediction_data.get(
        "timestamp_local"
    )  # for local file
    camera_id: str | None = prediction_data.get("camera_id")

    try:
        plate = prediction_data["results"][0]["plate"]
    except (KeyError, IndexError, TypeError):
        plate = None

    if not all((timestamp, timestamp_local, camera_id, plate)):
        logging.error(
            f"Missing required fields in prediction data: {json.dumps(json_data)}"
        )
        return "Invalid prediction data format.", 400

    # mypy: safe to cast after validation
    assert isinstance(timestamp, str)
    assert isinstance(timestamp_local, str)
    assert isinstance(camera_id, str)

    converted_payload = convert_plate_format_to_vehicle_format(json_data)

    data = {"json": json.dumps(converted_payload)}
    parkpow_token = os.getenv("PARKPOW_TOKEN")
    headers = {}
    if parkpow_token:
        headers = {"Authorization": f"Token {parkpow_token}"}

    activity_identifier = f"Camera: {camera_id} - Vehicle: {timestamp}"

    try:
        logging.info(f"{activity_identifier}. Sending webhook to {url}...")
        response = post_with_retries(url, data=data, files=all_files, headers=headers)
        try:
            response_json = json.loads(response.content)
            if not isinstance(response_json, list) or not response_json:
                raise ValueError("Response JSON is not a non-empty list")

            response_content = response_json[0]

            if not isinstance(response_content, dict):
                raise ValueError("First element of response JSON is not a dict")

        except (json.JSONDecodeError, IndexError, TypeError, ValueError) as parse_err:
            logging.error(
                f"{activity_identifier}. Failed to parse webhook response: {parse_err}. Raw content: {response.content!r}"
            )
            return f"Failed to parse webhook response: {parse_err}", 502

        logging.info(
            f"{activity_identifier}. Webhook response: {response.status_code} - {response_content['status']} - {response_content['id']}."
        )

    except requests.exceptions.RequestException as err:
        logging.error(f"{activity_identifier}. Error processing the request: {err}")
        return f"Failed to process the request: {err}", 500

    filename = get_jsonl_filename(camera_id, timestamp_local)

    try:
        logging.info(f"{activity_identifier}. Stripping data in local file...")
        strip_data_in_jsonl_file(
            os.path.join("/user-data", f"{filename}"),
            plate,
            converted_payload,
            camera_id,
            timestamp,
        )
        logging.info(
            f"{activity_identifier}. Data in JSONL file stripped successfully."
        )
    except Exception as e:
        logging.error(
            f"Error processing JSONL file for camera {activity_identifier}: {e}"
        )
        return f"Failed to process JSONL file: {e}", 500

    return "Request was successful", response.status_code
