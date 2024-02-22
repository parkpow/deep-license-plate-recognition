import argparse
import cgi
import json
import logging
import os
import sys
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError

import urllib3
from destinations.nx import Nx
from destinations.salient import SalientCompleteView

urllib3.disable_warnings()

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)


ENABLED_DESTINATIONS = [SalientCompleteView, Nx]


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, processor, *args, **kwargs):
        self.processor = processor
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

        for result in data["results"]:
            plate = result["plate"]
            if plate is not None:
                self.processor.process(
                    camera_id,
                    plate,
                    timestamp,
                )
        self.wfile.write(b"OK")


def main():
    parser = argparse.ArgumentParser(
        prog="Webhook Forwarder",
        description="Forward Webhook Events from Stream or Snapshot to a destinations.",
    )
    subparsers = parser.add_subparsers(help="Forward Destination")
    for destination in ENABLED_DESTINATIONS:
        lgr.info(f"Registering destination: {destination.name}")
        destination.add_cli_arguments(subparsers)

    args = parser.parse_args()

    destination_processor = args.func(args)
    handler = partial(RequestHandler, destination_processor)
    server = HTTPServer(("", 8001), handler)
    lgr.info("Starting Webhook Receiver Server, use <Ctrl-C> to stop")
    server.serve_forever()


if __name__ == "__main__":
    main()
