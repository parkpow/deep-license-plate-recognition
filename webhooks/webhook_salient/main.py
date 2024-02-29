import argparse
import cgi
import json
import logging
import os
import sys
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError

import requests
import urllib3
from requests.auth import HTTPBasicAuth

urllib3.disable_warnings()


LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

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


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, username, password, vms, camera, *args, **kwargs):
        self.username = username
        self.password = password
        self.vms = vms
        self.camera = camera
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Send a POST request instead.")
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        ctype, pdict = cgi.parse_header(self.headers["Content-Type"])
        if ctype == "multipart/form-data":
            pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
            fields = cgi.parse_multipart(self.rfile, pdict)
            # Get webhook content
            json_data = json.loads(fields.get("json")[0])

        else:
            raw_data = self.rfile.read(int(self.headers["content-length"])).decode(
                "utf-8"
            )
            if raw_data.startswith("json="):
                raw_data = raw_data[5:]
            try:
                json_data = json.loads(raw_data)
            except JSONDecodeError:
                json_data = {}

        lgr.debug("json_data:")
        lgr.debug(json_data)

        data = json_data["data"]
        camera_id = data["camera_id"]
        timestamp = data["timestamp"]

        # Pick first place from results
        plate = None
        for result in data["results"]:
            plate = result["plate"]
            break

        if plate is not None:
            notify_salient(
                self.username,
                self.password,
                self.vms,
                self.camera,
                camera_id,
                plate,
                timestamp,
            )

        self.wfile.write(b"OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Forward Stream Webhook Events to CompleteView VMS as Events."
    )
    parser.add_argument("--username", help="Recording Server Username.", required=True)
    parser.add_argument("--password", help="Recording Server Password.", required=True)
    parser.add_argument("--vms", help="Recording Server API Endpoint.", required=True)
    parser.add_argument(
        "--camera", help="UID of Camera used as Source of Events.", required=True
    )

    args = parser.parse_args()

    handler = partial(
        RequestHandler, args.username, args.password, args.vms, args.camera
    )
    server = HTTPServer(("", 8001), handler)
    lgr.info("Starting Webhook Receiver Server, use <Ctrl-C> to stop")
    server.serve_forever()
