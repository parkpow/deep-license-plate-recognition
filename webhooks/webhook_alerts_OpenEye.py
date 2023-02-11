"""
# Install flask
pip install Flask

# Run app
python3 file_name.py <parameter>

optional parameters:
--port
--debug

required parameters: 
--aki_token
--aks_token

for external access
--host=0.0.0.0

example:
python3 webhook_alerts_OpenEye.py --port=8001 --debug=1 --host==0.0.0.0 --aki_token=FDCER1234 --aks_token=abcdefghijklmnopqrstuvxz

"""


import argparse
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def handle_event():
    if request.method == "GET":
        return jsonify({"error": "Method not allowed"}), 405
    else:
        def convert_to_timestamp_microseconds(time_string):
            datetime_object = datetime.strptime(
                time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp_microseconds = int(datetime_object.timestamp() * 1000000)
            return timestamp_microseconds
        request_data = request.form['json']
        parsed_json = json.loads(request_data)
        url = "https://ows.openeye.net/api/monitoring/integration/event"
        payload = json.dumps({
            "requestDateMicros": convert_to_timestamp_microseconds(
                parsed_json['data']['timestamp']),
            "events": [
                {
                    "eventId": convert_to_timestamp_microseconds(
                        parsed_json['data']['timestamp']),
                    "eventDate": convert_to_timestamp_microseconds(
                        parsed_json['data']['timestamp']),
                    "eventType": "ANALYTIC_LICENSE_PLATE_DETECTED",
                    "attributes": {
                        "sourceObject": {
                            "type": "CAMERA",
                            "id": parsed_json['data']['camera_id']
                        },
                        "linkedObjects": [],
                        "props": [
                            {
                                "name": "licensePlate",
                                "value": parsed_json['data']['results'][0]['plate']
                            }
                        ]
                    }
                }
            ]
        })

        headers = {
            'Authorization': '!EXT-INTEGRATOR AKI={},AKS={}'.format(args.aki_token, args.aks_token),
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 202:
            print(response.status_code)
            return jsonify({"sucessus": "request sent"}), response.status_code
        else:
            print(response.status_code)
            print(json.loads(response.text))
            return jsonify(response.text), response.status_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Webhook server to receive JSON on /note route.")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="The host IP address to bind the server to.")
    parser.add_argument("--port", type=int, default=5000,
                        help="The port number to bind the server to. (Optional - Default = 5000)")
    parser.add_argument("--debug", type=int, default=0,
                        help="Turn on Flask debug mode. (Optional)")
    parser.add_argument("--aki_token", type=str, required=True,
                        help="To get the AKI, in OWS you would go into Management > Integrations > Event Receiver API (Analytics) then choose API Access Keys.")
    parser.add_argument("--aks_token", type=str, required=True,
                        help="To get the AKS, in OWS you would go into Management > I\ntegrations > Event Receiver API (Analytics) then choose API Access Keys, The AKS is normally only shown one time, when you first generate the key.")
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=bool(args.debug))
