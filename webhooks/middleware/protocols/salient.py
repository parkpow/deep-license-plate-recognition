import logging
import os
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

lgr = logging.getLogger(__name__)


def notify_salient(
    username, password, vms_api, camera_uid, source, description, timestamp
):
    lgr.debug(
        f"Notify CompleteView Source: {source}, Description: {description}, timestamp: {timestamp}"
    )
    endpoint = "/v2.0/events"

    try:
        res = requests.post(
            vms_api + endpoint,
            json={
                "events": [
                    {
                        "entityType": 1,
                        "eventType": 58,
                        "eventDescription": f"Plate Detection [{description}]",
                        "user": f"Platerecognizer({source})",
                        "deviceGuid": camera_uid,
                    }
                ]
            },
            auth=HTTPBasicAuth(username, password),
            verify=False,
        )
        res.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        lgr.error("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        lgr.error("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        lgr.error("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        lgr.error("Oops: Something Else", err)


def process_request(
    json_data: dict[str, Any], upload_file: bytes | None = None
) -> tuple[str, int]:
    username = os.getenv("VMS_USERNAME")
    password = os.getenv("VMS_PASSWORD")
    vms_api_url = os.getenv("VMS_API_URL")
    camera_uid = os.getenv("CAMERA_UID")

    data = json_data.get("data", {})
    camera_id = data.get("camera_id", "")
    timestamp = data.get("timestamp", "")

    plate = None
    for result in data.get("results", []):
        plate = result.get("plate")
        if plate and type(plate) != str:
            plate = result["props"]["plate"][0]["value"]
        break

    if plate:
        try:
            notify_salient(
                username, password, vms_api_url, camera_uid, camera_id, plate, timestamp
            )
        except Exception as e:
            return f"Failed to notify Salient: {e}", 400

    return "OK", 200
