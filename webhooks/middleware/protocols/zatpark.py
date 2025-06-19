import base64
import os
import logging
from datetime import datetime
from typing import Any

import requests

service_url = os.getenv("ZATPARK_SERVICE_URL")

if not service_url:
    logging.error(
        "Missing required configuration: ZATPARK_SERVICE_URL must be set."
    )
    exit(1)

def convert_to_timestamp(time_string: str) -> int:
    try:
        if "T" in time_string and time_string.endswith("Z"):
            time_string = time_string.replace("Z", "+00:00")
            dt = datetime.fromisoformat(time_string)
        else:
            dt = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S.%f%z")
        return int(dt.timestamp())
    except Exception as e:
        raise ValueError(f"Invalid time format: {time_string}") from e

def extract_data_plate(json_data: dict) -> tuple[
    str | None, str | None, float | None, str | None, str | None, dict[str, str], int, int
]:
    data_results = json_data["data"]["results"][0]
        
    plate = data_results.get("plate")
    region = data_results.get("region", {}).get("code")
    score = data_results.get("score")
    orientation = data_results.get("orientation", [{}])[0].get("orientation")
    
    # Common data extraction
    camera_id = json_data["data"]["camera_id"]
    timestamp_local = convert_to_timestamp(json_data["data"]["timestamp_local"])
    timestamp = convert_to_timestamp(json_data["data"]["timestamp"])
    header = json_data.get("webhook_header", {})

    # This block handles the 'vehicle' detection_mode
    if isinstance(plate, dict) and "props" in plate:
        plate_props = data_results["plate"]["props"]
        vehicle_props = data_results.get("vehicle", {}).get("props", {})

        plate = plate_props.get("plate", [{}])[0].get("value")
        score = plate_props.get("plate", [{}])[0].get("score")
        region = plate_props.get("region", [{}])[0].get("value")
        orientation = vehicle_props.get("orientation", [{}])[0].get("value")

    return region, plate, score, orientation, camera_id, header, timestamp, timestamp_local


def process_request(
     json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
    ) -> tuple[str, int]:

    if not all_files:
        logging.error("No files dictionary provided. 'vehicle' and 'plate' image_type are required.")
        return "No files uploaded.", 400
    
    upload_file = all_files.get("upload")
    plate_img = all_files.get("plate_img")
    
    if not upload_file or not plate_img:
        logging.error("Both image_type are required,  vehicle and plate.")
        return "Required files ('vehicle' or 'plate') are missing.", 400

    imagens = {}
    if upload_file:
        imagens['upload'] = base64.b64encode(upload_file).decode("utf-8")
    if plate_img:
        imagens['plate'] = base64.b64encode(plate_img).decode("utf-8")

    region, plate, score, orientation, camera_id, header, timestamp, timestamp_local = extract_data_plate(json_data)

    mac_address = header.get("mac_address")
    camera_name = header.get("camera_name") or camera_id
    serial_number = header.get("serial_number") or mac_address

    if mac_address is None:
        logging.error(f"The MAC address is required for '{camera_id}', but was not provided.")
        return "The MAC address is required.", 400
    

    if not plate or score is None:
        logging.error("Failed to extract plate or score from json_data.")
        return "Failed to extract required data.", 400

    payload = {
        "decodes": [
            {
                "vrm": plate.upper(),
                "serialNo": serial_number,
                "MAC": mac_address,
                "cameraName": camera_name,
                "timeStamp": {
                    "Time": timestamp,
                    "LocalTime": timestamp_local
                },
                "confidence": int(score * 100),
                "motion": "toward" if orientation == "Front" else "Away",
                "plate": imagens['plate'],
                "overview": imagens['upload']
            }
        ]
    }

    try:
        response = requests.post(service_url, json=payload, timeout=10)
        response.raise_for_status()

        try:
            response_json = response.json()
            logging.info(f"Server response: {response_json}")
        except ValueError:
            logging.warning(f"Response is not a valid JSON. Content: {response.text}")

        return "Request received and successfully processed.", 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send request: {str(e)}")
        return f"Failed to process request: {str(e)}", 500
