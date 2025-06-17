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


def convert_to_timestamp_microseconds(time_string):
    datetime_object = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp_microseconds = int(datetime_object.timestamp() * 1000000)
    return timestamp_microseconds


def extract_data_plate(json_data: dict) -> tuple[str | None, str | None]:
    plate = json_data["data"]["results"][0]["plate"]
    region = json_data["data"]["results"][0].get("region", {}).get("code")
    score = json_data["data"]["results"][0].get("score")
    orientation = json_data["data"]["results"][0].get("orientation", [{}])[0].get("orientation")
    camera_id = json_data["data"]["camera_id"]
    
    header = json_data.get("webhook_header", {})


    if plate and type(plate) != str:
        plate = json_data["data"]["results"][0]["plate"]["props"]["plate"][0]["value"]
        orientation = json_data["data"]["results"][0]["vehicle"]["props"]["orientation"][0]["value"]
        region = json_data["data"]["results"][0]["plate"]["props"]["region"][0]["value"]
        score = json_data["data"]["results"][0]["plate"]["props"]["plate"][0]["score"]
        camera_id = json_data["data"]["camera_id"]
        header = json_data.get("webhook_header", {})

    return region, plate, score, orientation, camera_id, header


def process_request(
     json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
    ) -> tuple[str, int]:


    if not all_files:
        logging.error("No files dictionary provided. 'upload' and 'plate_img' are required.")
        return "No files uploaded.", 400

    upload_file = all_files.get("upload")
    plate_img = all_files.get("plate_img")
    
    if not upload_file or not plate_img:
        logging.error("Both 'upload' and 'plate_img' files must be provided. They are required.")
        return "Required files ('upload' or 'plate_img') are missing.", 400
        logging.error("Both 'upload' and 'plate_img' must be provided. They are required.")
        return "No files uploaded.", 400

    imagens = {}
    if upload_file:
        imagens['upload'] = base64.b64encode(upload_file).decode("utf-8")
    if plate_img:
        imagens['plate'] = base64.b64encode(plate_img).decode("utf-8")

    region, plate, score, orientation, camera_id, header = extract_data_plate(json_data)

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
                    "Time": int(datetime.now().timestamp()),
                    "LocalTime": int(datetime.now().timestamp())
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
