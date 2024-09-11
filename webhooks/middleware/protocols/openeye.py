import json
import os
from datetime import datetime
from typing import Any

import requests


def convert_to_timestamp_microseconds(time_string):
    datetime_object = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp_microseconds = int(datetime_object.timestamp() * 1000000)
    return timestamp_microseconds


def process_request(
    json_data: dict[str, Any], upload_file: bytes | None = None
) -> tuple[str, int]:
    # Prepare the payload for the API request
    payload = json.dumps(
        {
            "requestDateMicros": convert_to_timestamp_microseconds(
                json_data["data"]["timestamp"]
            ),
            "events": [
                {
                    "eventId": convert_to_timestamp_microseconds(
                        json_data["data"]["timestamp"]
                    ),
                    "eventDate": convert_to_timestamp_microseconds(
                        json_data["data"]["timestamp"]
                    ),
                    "eventType": "ANALYTIC_LICENSE_PLATE_DETECTED",
                    "attributes": {
                        "sourceObject": {
                            "type": "CAMERA",
                            "id": json_data["data"]["camera_id"],
                        },
                        "linkedObjects": [],
                        "props": [
                            {
                                "name": "licensePlate",
                                "value": json_data["data"]["results"][0]["plate"],
                            }
                        ],
                    },
                }
            ],
        }
    )

    # Headers for the request
    aki_token = os.getenv("AKI_TOKEN")
    aks_token = os.getenv("AKS_TOKEN")
    url = "https://ows.openeye.net/api/monitoring/integration/event"

    headers = {
        "Authorization": f"!EXT-INTEGRATOR AKI={aki_token},AKS={aks_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return "Request sent successfully.", response.status_code
    except requests.exceptions.HTTPError as err:
        print(err)
        return f"Failed to send request: {err}", 400
