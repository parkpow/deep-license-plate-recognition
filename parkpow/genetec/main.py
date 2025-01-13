import argparse
import cgi
import json
import logging
import os
import sys
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue

import urllib3
from api import ParkPowApi, Snapshot

urllib3.disable_warnings()

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)


def confidence_score(value: str):
    return int(value) / 100


class WebhookQueue:
    def __init__(self, api, max_workers=4):
        self.queue = Queue()
        self.api = api
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def enqueue(self, data, params):
        camera_id = data["CameraName"]
        image_base_64 = data["ContextImage"]
        date_utc = data["DateUtc"]
        time_utc = data["TimeUtc"]
        created_date = datetime.strptime(
            f"{date_utc} {time_utc}", "%d/%m/%Y %H:%M:%S"
        ).replace(tzinfo=timezone.utc)

        # created_date = datetime.now() uncomment for testing
        if isinstance(self.api, ParkPowApi):
            v_attrs = data["Attributes"]
            plate_confidence = confidence_score(data["ConfidenceScore"])
            event_data = {
                "camera": camera_id,
                "image": image_base_64,
                "results": [
                    {
                        "plate": {
                            "score": plate_confidence,
                            "type": "Plate",
                            "props": {
                                "plate": [
                                    {"value": data["Plate"], "score": plate_confidence}
                                ],
                                "region": [
                                    {
                                        "value": data["State"],
                                        "score": confidence_score(
                                            v_attrs["State Name Confidence Score"]
                                        ),
                                    }
                                ],
                            },
                        },
                        "vehicle": {
                            "score": confidence_score(v_attrs["Confidence Score"]),
                            # "type": "Sedan", Todo map ['Vehicle Type'] to PP vehicle types
                            "props": {
                                "color": [
                                    {
                                        "score": confidence_score(
                                            v_attrs["State Name Confidence Score"]
                                        ),
                                        "value": v_attrs[
                                            "Vehicle Color"
                                        ],  # Todo map ['Vehicle Color'] to PP color types
                                    }
                                ],
                                "orientation": [
                                    {
                                        "score": 1,
                                        "value": "Rear"
                                        if v_attrs["Relative Motion"] == "Moving Away"
                                        else "Front",
                                    }
                                ],
                                "make_model": [
                                    {
                                        "make": v_attrs["Vehicle Make"],
                                        "score": 1,
                                        "model": v_attrs["Vehicle Model"],
                                    }
                                ],
                            },
                        },
                    }
                ],
                "time": created_date.strftime("%Y-%m-%d %H:%M:%S.%f%z"),
            }

        elif isinstance(self.api, Snapshot):
            event_data = {
                "upload": image_base_64,
                "timestamp": created_date.isoformat(),
            }
            # include extra params in URL
            if "camera_id" in params:
                event_data["camera_id"] = params["camera_id"][0]
            else:
                event_data["camera_id"] = camera_id
            if "mmc" in params:
                event_data["mmc"] = params["mmc"][0]
            else:
                event_data["mmc"] = "true"
            if "regions" in params:
                event_data["regions"] = params["regions"][0]

            if "config" in params:
                event_data["config"] = params["config"][0]

        else:
            # should never happen
            raise NotImplementedError

        lgr.debug("send to queue")
        self.queue.put(event_data)

    def process(self):
        while True:
            data = self.queue.get()
            lgr.debug(f"Processing message: {data}")
            if isinstance(self.api, ParkPowApi):
                self.api.log_vehicle(data)
            elif isinstance(self.api, Snapshot):
                self.api.recognition(data)
            else:
                # should never happen
                raise NotImplementedError


class Genetec:
    @staticmethod
    def validate(data) -> bool:
        required_keys = ("CameraName", "ContextImage", "DateUtc", "TimeUtc")
        return all(k in data for k in required_keys)


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, wq: WebhookQueue, *args, **kwargs):
        self.wq = wq
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Send a POST request instead.")
        return

    def do_POST(self):
        """
        Download and queue Genetec webhooks for forwarding
        :return:
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        ctype, pdict = cgi.parse_header(self.headers["Content-Type"])
        if ctype != "application/json":
            res = f"Unexpected content type: {ctype}"
            lgr.error(res)

        content_length = int(self.headers["content-length"])
        if content_length > 0:
            raw_data = self.rfile.read(content_length).decode("utf-8")
            lgr.debug(f"raw_data: {raw_data}")
            data = json.loads(raw_data)
            if Genetec.validate(data):
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                self.wq.enqueue(data, params)
                res = "OK"
            else:
                res = "Unexpected Genetec Format"
        else:
            res = f"Unexpected content length: {content_length}"
            lgr.error(res)
        self.wfile.write(res.encode())


def server_worker(wq):
    port = 8002
    handler = partial(RequestHandler, wq)
    server = HTTPServer(("", port), handler)
    lgr.info(f"Starting Webhook Receiver on port: {port}, use <Ctrl-C> to stop")
    server.serve_forever()


def forward_parkpow(args):
    parkpow = ParkPowApi(args.token, args.url)
    return WebhookQueue(parkpow)


def forward_snapshot(args):
    snapshot = Snapshot(args.token, args.url)
    return WebhookQueue(snapshot)


def main():
    parser = argparse.ArgumentParser(
        description="Forward Genetec LPR Events to ParkPow."
    )
    subparsers = parser.add_subparsers(help="subcommand help")
    pp_args = subparsers.add_parser(
        "parkpow",
        help="Forward Genetec events to ParkPow",
    )
    pp_args.add_argument("--token", help="ParkPow Token.", required=True)
    pp_args.add_argument("--url", help="ParkPow Server URL.", required=False)
    pp_args.set_defaults(func=forward_parkpow)

    snapshot_args = subparsers.add_parser(
        "snapshot",
        help="Forward Genetec events to Snapshot",
    )
    group = snapshot_args.add_mutually_exclusive_group()
    group.add_argument("--url", help="Snapshot Server URL.")
    group.add_argument("--token", help="Snapshot Token.")
    snapshot_args.set_defaults(func=forward_snapshot)

    parsed_args = parser.parse_args()
    webhook_queue = parsed_args.func(parsed_args)
    monitor = threading.Thread(target=webhook_queue.process, args=())
    server_thread = threading.Thread(target=server_worker, args=(webhook_queue,))
    monitor.start()
    server_thread.start()


if __name__ == "__main__":
    main()
