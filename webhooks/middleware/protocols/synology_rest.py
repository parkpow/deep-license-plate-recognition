import logging
import os
from typing import Any
from urllib import parse

import dateutil.parser as dp
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_request(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
) -> tuple[str, int]:
    url = os.getenv("REST_SERVICE_URL", "")

    timestamp = json_data["data"]["timestamp_local"]
    plate = json_data["data"]["results"][0].get("plate")
    if plate and type(plate) != str:
        plate = json_data["data"]["results"][0]["plate"]["props"]["plate"][0]["value"]

    try:
        parsed_date_time = dp.parse(timestamp)
        timestamp = str(int(parsed_date_time.timestamp()))
    except ValueError:
        logging.error(f"Vehicle: {plate}. Invalid timestamp format.")
        return "Invalid timestamp format.", 400

    request_data = {"time": timestamp, "text1": plate}

    HEADERS = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
    data = parse.urlencode(request_data)

    response = requests.post(url=url, headers=HEADERS, data=data, verify=False)

    if response.status_code == 200:
        logging.info(f"Vehicle: {plate}. REST request successful.")
        return "REST request successful.", response.status_code
    else:
        logging.error(
            f"Vehicle: {plate}. REST request failed. Response code: {response.status_code}"
        )
        return (
            f"REST request failed. Response code: {response.status_code}",
            response.status_code,
        )
