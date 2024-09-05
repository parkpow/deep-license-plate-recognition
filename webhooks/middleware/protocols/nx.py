import csv
import json
import logging
import os
import sys
from datetime import datetime
from threading import Timer
from typing import Any

import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)

session = requests.Session()


def convert_to_timestamp_milliseconds(time_string):
    data_hora = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S.%f%z")
    timestamp_milissegundos = int(data_hora.timestamp() * 1000)
    return timestamp_milissegundos


def session_create(login, password, server_host, ssl):
    url = f"{server_host}/rest/v2/login/sessions"
    payload = {"username": login, "password": password, "setCookie": True}
    headers = {
        "Content-Type": "application/json",
    }
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


def server_info(server_host, ssl):
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


def parkpow_get_tags(parkpow_token, tag):
    url = "https://app.parkpow.com/api/v1/vehicles/"
    querystring = {"tags": f"{tag}"}
    headers = {"Authorization": f"Token {parkpow_token}"}

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        parsed_json = json.loads(response.text)

        if "results" in parsed_json:
            with open("list.csv", "w", newline="") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(["license_plate"])

                for result in parsed_json["results"]:
                    if "license_plate" in result:
                        license_plate = result["license_plate"].upper()
                        csv_writer.writerow([license_plate])

        logging.info("List tag information successfully updated.")
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to retrieve Parkpow information: {err}")
        sys.exit(1)

    renew_timer = Timer(20, lambda: parkpow_get_tags(parkpow_token, tag))
    renew_timer.start()


def parkpow_check_license(license_plate):
    try:
        with open("list.csv") as csv_file:
            return True if license_plate in csv_file.read() else False
    except FileNotFoundError:
        return False


def process_request(
    json_data: dict[str, Any], upload_file: bytes | None = None
) -> tuple[str, int]:
    server_host = os.getenv("SERVER_HOST")
    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")
    ssl = os.getenv("SSL", "False").lower() in ("true", "1", "t")
    os.getenv("PARKPOW_TOKEN")
    tag = os.getenv("TAG")

    # Ensure the necessary environment variables are set
    if not server_host or not login or not password:
        logging.error(
            "Missing required configuration: server_host, password, and login must be set."
        )
        return "Missing required configuration", 500

    session_create(login, password, server_host, ssl)
    server_id = server_info(server_host, ssl)

    license_plate = json_data["data"]["results"][0]["plate"].upper()
    url = f"{server_host}/rest/v2/devices/{json_data['data']['camera_id']}/bookmarks"
    payload = {
        "serverId": server_id,
        "name": license_plate,
        "description": tag.upper()
        if parkpow_check_license(license_plate) and tag
        else "",
        "startTimeMs": convert_to_timestamp_milliseconds(
            json_data["data"]["timestamp_local"]
        ),
        "durationMs": 5000,
        "tags": [tag] if parkpow_check_license(license_plate) else ["Stream"],
        "creationTimeMs": 0,
    }
    headers = {
        "Content-Type": "application/json",
    }
    try:
        response = session.post(url, json=payload, headers=headers, verify=ssl)
        response.raise_for_status()
        logging.info("Request was successful.")
        return "Request was successful", 200
    except requests.exceptions.RequestException as err:
        logging.error(f"Error processing the request: {err}")
        return f"Failed to process the request: {err}", 400
