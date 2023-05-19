"""
# Install
Check instructions in:
https://github.com/parkpow/deep-license-plate-recognition/blob/master/webhooks/README.md#integrations
"""


import argparse
import json
import os
import sys
from datetime import datetime

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


def convert_to_timestamp_microseconds(time_string):
    datetime_object = datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp_microseconds = int(datetime_object.timestamp() * 1000000)
    return timestamp_microseconds


@app.route("/", methods=["GET", "POST"])
def handle_event():
    if request.method == "GET":
        return jsonify({"error": "Method not allowed"}), 405
    else:

        request_data = request.form["json"]
        parsed_json = json.loads(request_data)
        url = "https://ows.openeye.net/api/monitoring/integration/event"
        payload = json.dumps(
            {
                "requestDateMicros": convert_to_timestamp_microseconds(
                    parsed_json["data"]["timestamp"]
                ),
                "events": [
                    {
                        "eventId": convert_to_timestamp_microseconds(
                            parsed_json["data"]["timestamp"]
                        ),
                        "eventDate": convert_to_timestamp_microseconds(
                            parsed_json["data"]["timestamp"]
                        ),
                        "eventType": "ANALYTIC_LICENSE_PLATE_DETECTED",
                        "attributes": {
                            "sourceObject": {
                                "type": "CAMERA",
                                "id": parsed_json["data"]["camera_id"],
                            },
                            "linkedObjects": [],
                            "props": [
                                {
                                    "name": "licensePlate",
                                    "value": parsed_json["data"]["results"][0]["plate"],
                                }
                            ],
                        },
                    }
                ],
            }
        )

        headers = {
            "Authorization": f"!EXT-INTEGRATOR AKI={aki_token},AKS={aks_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return jsonify({"sucessus": "request sent"}), response.status_code
        except requests.exceptions.HTTPError as err:
            print(err)
            raise SystemExit(err) from err


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Webhook server to receive JSON on /note route."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="The host IP address to bind the server to.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="The port number to bind the server to. (Optional - Default = 5000)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Turn on Flask debug mode. (Optional)"
    )
    parser.add_argument(
        "--aki_token",
        type=str,
        help="To get the AKI, in OWS you would go into Management > Integrations > Event Receiver API (Analytics) then choose API Access Keys.",
    )
    parser.add_argument(
        "--aks_token",
        type=str,
        help="To get the AKS, in OWS you would go into Management > I\ntegrations > Event Receiver API (Analytics) then choose API Access Keys, The AKS is normally only shown one time, when you first generate the key.",
    )
    args = parser.parse_args()

    aki_token = os.getenv("AKI_TOKEN", args.aki_token)
    aks_token = os.getenv("AKS_TOKEN", args.aks_token)

    if aki_token is None or aks_token is None:
        print("Variables AKI_TOKEN and AKS_TOKEN are required.")
        sys.exit(1)
    app.run(host=args.host, port=args.port, debug=bool(os.getenv("DEBUG", args.debug)))
