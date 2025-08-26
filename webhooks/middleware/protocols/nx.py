# middleware_nx.py
import csv
import json
import logging
import os
import sys
from datetime import datetime
from threading import Timer
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)

session = requests.Session()

parkpow_license_plates = set()


def convert_to_timestamp_milliseconds(time_string: str) -> int:
    data_hora = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S.%f%z")
    return int(data_hora.timestamp() * 1000)


def session_create(login: str, password: str, server_host: str, ssl: bool) -> None:
    url = f"{server_host}/rest/v2/login/sessions"
    payload = {"username": login, "password": password, "setCookie": True}
    headers = {"Content-Type": "application/json"}
    try:
        response = session.post(url, json=payload, headers=headers, verify=ssl)
        response.raise_for_status()
        logging.info("Session created successfully.")
    except requests.exceptions.RequestException as err:
        logging.error(f"Session creation failed: {err}")
        sys.exit(1)

    renew_timer = Timer(
        3600 * 24, lambda: session_create(login, password, server_host, ssl)
    )
    renew_timer.start()


def server_info(server_host: str, ssl: bool) -> str:
    url = f"{server_host}/rest/v2/servers/"
    try:
        response = session.get(url, verify=ssl)
        response.raise_for_status()
        parsed_json = json.loads(response.text)
        logging.info("Server ID: %s", parsed_json[0]["id"])
        return parsed_json[0]["id"][1:-1]
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to retrieve server information: {err}")
        sys.exit(1)


def parkpow_get_tags(parkpow_token: str, tag: str) -> None:
    url = "https://app.parkpow.com/api/v1/vehicles/"
    querystring = {"tags": tag}
    headers = {"Authorization": f"Token {parkpow_token}"}

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        parsed_json = json.loads(response.text)

        global parkpow_license_plates
        parkpow_license_plates.clear()

        if "results" in parsed_json:
            with open("list.csv", "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["license_plate"])

                for result in parsed_json["results"]:
                    if "license_plate" in result:
                        license_plate = result["license_plate"].upper()
                        parkpow_license_plates.add(license_plate)  # Store in-memory
                        csv_writer.writerow([license_plate])

        logging.info("Parkpow tag information successfully updated.")
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to retrieve Parkpow information: {err}")
        sys.exit(1)

    renew_timer = Timer(1200, lambda: parkpow_get_tags(parkpow_token, tag))
    renew_timer.start()


def parkpow_check_license(license_plate: str) -> bool:
    if license_plate in parkpow_license_plates:
        return True

    try:
        with open("list.csv") as csv_file:
            return license_plate.upper() in csv_file.read()
    except FileNotFoundError:
        logging.error(
            "list.csv not found. Ensure Parkpow tags are retrieved successfully."
        )
        return False


def process_request(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
) -> tuple[str, int]:
    server_host = os.getenv("SERVER_HOST")
    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    ssl = os.getenv("SSL", "False").lower() in ("true", "1", "t")
    tag = os.getenv("TAG")

    plate = json_data["data"]["results"][0].get("plate")
    if plate and type(plate) != str:
        plate = json_data["data"]["results"][0]["plate"]["props"]["plate"][0]["value"]

    # Ensure the necessary environment variables are set
    if not server_host or not login or not password:
        logging.error(
            "Missing required configuration: server_host, password, and login must be set."
        )
        return "Missing required configuration", 500

    session_create(login, password, server_host, ssl)
    server_id = server_info(server_host, ssl)

    license_plate = plate.upper()
    url = f"{server_host}/rest/v2/devices/{json_data['data']['camera_id']}/bookmarks"
    payload = {
        "serverId": server_id,
        "name": license_plate,
        "description": (
            tag.upper() if parkpow_check_license(license_plate) and tag else ""
        ),
        "startTimeMs": convert_to_timestamp_milliseconds(
            json_data["data"]["timestamp_local"]
        ),
        "durationMs": 5000,
        "tags": [tag] if parkpow_check_license(license_plate) else ["Stream"],
        "creationTimeMs": 0,
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = session.post(url, json=payload, headers=headers, verify=ssl)
        response.raise_for_status()
        logging.info(f"Vehicle: {plate}. Request was successful.")
        return "Request was successful", response.status_code
    except requests.exceptions.RequestException as err:
        logging.error(f"Vehicle: {plate}.Error processing the request: {err}")
        return f"Failed to process the request: {err}", 400


def initialize_parkpow_tags() -> None:
    parkpow_token = os.getenv("PARKPOW_TOKEN")
    tag = os.getenv("TAG")

    if parkpow_token and tag:
        parkpow_get_tags(parkpow_token, tag)
    else:
        logging.error("PARKPOW_TOKEN and TAG must be set to initialize Parkpow tags.")
