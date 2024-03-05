import argparse
import json
import os
import sys
import logging
from datetime import datetime
from threading import Timer
import csv
import requests
import requests.cookies
import urllib3
from flask import Flask, jsonify, request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = requests.Session()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s') 


app = Flask(__name__)


def convert_to_timestamp_milliseconds(time_string):
    data_hora = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S.%f%z")
    timestamp_milissegundos = int(data_hora.timestamp() * 1000)

    return timestamp_milissegundos


def session_create(args):
    url = f"{server_host}/rest/v2/login/sessions"
    payload = {
        "username": args.login,
        "password": args.password,
        "setCookie": True
    }
    headers = {
        "Content-Type": "application/json",
    }
    try:
        response = session.post(url, json=payload, headers=headers, verify=args.ssl)
        response.raise_for_status()
        logging.info("Session created successfully.")
    except requests.exceptions.RequestException as err:
        logging.error(f"Session creation failed: {err}")
        sys.exit(1)

    renew_timer = Timer(3600 * 24, lambda: session_create(args))  
    renew_timer.start()


def server_info(args):
    url = f"{server_host}/rest/v2/servers/"
    try:
        response = session.get(url, verify=args.ssl)
        response.raise_for_status()
        parsed_json = json.loads(response.text)
        logging.info("Server ID: %s", parsed_json[0]["id"])
        return parsed_json[0]["id"][1:-1]
    except requests.exceptions.RequestException as err:
        logging.error(f"Failed to retrieve server information: {err}")
        sys.exit(1)


def parkpow_get_tags(args):
    url = "https://app.parkpow.com/api/v1/vehicles/"
    querystring = {"tags": f"{args.tag}"}
    headers = {"Authorization": f"Token {args.parkpow_token}"}

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

    renew_timer = Timer(20, lambda: parkpow_get_tags(args))
    renew_timer.start()


def parkpow_check_license(license_plate):
    try:
        with open("list.csv", "r") as csv_file:
            return True if license_plate in csv_file.read() else False
    except FileNotFoundError:
        return False


@app.route("/", methods=["POST"])
def handle_event():
    request_data = request.form.get("json")
    if request_data is None:
        return jsonify({"error": "JSON data not found in the request"}), 400

    try:
        parsed_json = json.loads(request_data)
      
        url = f"{server_host}/rest/v2/devices/{parsed_json['data']['camera_id']}/bookmarks"
        license_plate = parsed_json["data"]["results"][0]["plate"].upper()
        payload = {
            "serverId": server_id,
            "name": license_plate,
            "description": args.tag.upper() if parkpow_check_license(license_plate) else "",
            "startTimeMs": convert_to_timestamp_milliseconds(parsed_json["data"]["timestamp_local"]),
            "durationMs": 5000,
            "tags": [args.tag] if parkpow_check_license(license_plate) else ["Stream"],
            "creationTimeMs": 0
        }
        headers = {
            "Content-Type": "application/json",
        }
        response = session.post(url, json=payload, headers=headers, verify=args.ssl)
        if response.status_code == 200:
            logging.info("Request was successful. Response code: 200")
        else:
            logging.warning(f"Request returned status code: {response.status_code}")

        response.raise_for_status()
        return jsonify({"success": "request sent"}), response.status_code
    except (json.JSONDecodeError, requests.exceptions.RequestException) as err:
        logging.error(f"Error processing the request: {err}")
        return jsonify({"error": "Failed to process the request"}), 500


if __name__ == "__main__":

    from waitress import serve
    parser = argparse.ArgumentParser(description="Webhook server to receive JSON on /note route.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="The host IP address to bind the server to.")
    parser.add_argument("--port", type=int, default=5000, help="The port number to bind the server to. (Optional - Default = 5000)")
    parser.add_argument("--debug", action="store_true", help="Turn on Flask debug mode. (Optional)")
    parser.add_argument("--server_host", type=str, help="Server host")
    parser.add_argument("--login", type=str, help="login")
    parser.add_argument("--password", type=str, help="password")
    parser.add_argument("--ssl", type=bool, default=False, help="Enable ssl verification (boolean)")
    parser.add_argument("--parkpow_token", type=str, help="Token Parkpow")
    parser.add_argument("--tag", type=str, help="Parkpow TAG")

    args = parser.parse_args()

    server_host = os.getenv("SERVER_HOST", args.server_host)
    args.login = os.getenv("LOGIN", args.login)
    args.password = os.getenv("PASSWORD", args.password)
    args.ssl = os.getenv("SSL", args.ssl)
    args.debug = os.getenv("DEBUG", args.debug)
    args.tag = os.getenv("TAG", args.tag)
    args.parkpow_token = os.getenv("PARKPOW_TOKEN", args.parkpow_token)


    if server_host is None or args.password is None or args.login is None:
        logging.error("Variables server_host, password and login are required.")
        sys.exit(1)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.tag or args.parkpow_token:
        if args.tag is None or args.parkpow_token is None:
            logging.error("Variables tag and parkpow_token are required to activate")
            sys.exit(1)
        else:
            parkpow_get_tags(args)

    session_create(args)
    server_id = server_info(args)

    serve(app, host=args.host, port=args.port)
    