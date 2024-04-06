import argparse
import cgi
import json
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from queue import Queue

import requests
import urllib3

urllib3.disable_warnings()

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)


class WebhookQueue:
    def __init__(self, api_key, token, pp_url, max_workers=4):
        self.api_key = api_key
        self.token = token
        self.pp_url = pp_url

        self.queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def enqueue(self, message):
        self.queue.put(message)

    def log_vehicle(self, image, license_plate_number, confidence, camera, time):
        try:
            res = requests.post(
                "https://app.parkpow.com/api/v1/log-vehicle/",
                headers={"Authorization": f"Token {self.token}"},
                json={
                    "camera": camera,
                    "image": image,
                    "results": [
                        {
                            "plate": {
                                "box": {
                                    "xmin": None,
                                    "ymin": None,
                                    "ymax": None,
                                    "xmax": None,
                                },
                                "score": confidence,
                                "type": license_plate_number,
                                "props": None,
                            },
                            "direction": None,
                            "position_sec": None,
                            "vehicle": {
                                "box": {
                                    "xmin": None,
                                    "ymin": None,
                                    "ymax": None,
                                    "xmax": None,
                                },
                                "score": 0.0,
                                "type": "Sedan",
                                "props": {
                                    "color": None,
                                    "orientation": None,
                                    "make_model": None,
                                },
                            },
                        }
                    ],
                    "time": time,
                },
            )
            lgr.debug(f"res: {res}")
            print(res.text)
            res.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            lgr.error("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            lgr.error("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            lgr.error("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            lgr.error("Oops: Something Else", err)

    def process(self):
        while True:
            data = self.queue.get()
            lgr.info(f"Processing message: {data}")
            camera_id = data["camera_id"]
            created = data["created"]
            confidence = data["confidence"]
            license_plate_number = data["license_plate_number"]

            image = self.get_thumbnail_image(camera_id, created)

            self.log_vehicle(image, license_plate_number, confidence)

    def get_thumbnail_image(self, camera_id, timestamp, resolution="hi-res"):
        """
        Extract thumbnails from cameras, thumbnail's associated timestamp will be as close
        as possible to the user-specified timestamp but may differ by up to 10 seconds
        (when no motion has been detected).
        :param camera_id: The unique identifier of the camera.
        :param timestamp: The approximate timestamp of the requested thumbnail.
                Formatted as a Unix timestamp in seconds.
                Defaults to the current time.
        :param resolution: `low-res` or `hi-res`
        :return: returns the binary data of a JPEG image
        """
        url = "https://api.verkada.com/cameras/v1/footage/thumbnails"

        params = {
            "resolution": resolution,
            "camera_id": camera_id,
            "timestamp": timestamp,
        }

        headers = {"x-api-key": self.api_key}
        requests.get(url, headers=headers, params=params)


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
        Your endpoint have 2 seconds to respond to a notification.
        If your endpoint don't send a response inside that time,
        the notification is treated as failed and will be retried only once.
        :return:
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # TODO Replace parsing with CGI https://peps.python.org/pep-0594/#cgi
        ctype, pdict = cgi.parse_header(self.headers["Content-Type"])
        if ctype != "application/json":
            lgr.error(f"Unexpected content type: {ctype}")
            self.wfile.write(b"OK")

        content_length = int(self.headers["content-length"])
        raw_data = self.rfile.read(content_length).decode("utf-8")
        lgr.debug(f"raw_data: {raw_data}")
        json_data = json.loads(raw_data)
        webhook_type = json_data["webhook_type"]
        if webhook_type != "lpr":
            lgr.error(f"Unexpected webhook type: {webhook_type}")
            self.wfile.write(b"OK")

        data = json_data["data"]
        print("send to queue")
        self.wq.enqueue(data)
        self.wfile.write(b"OK")


def server_worker(wq):
    handler = partial(RequestHandler, wq)
    server = HTTPServer(("", 8001), handler)
    lgr.info("Starting Webhook Receiver, use <Ctrl-C> to stop")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Forward Verkada LPR Webhook Events to ParkPow."
    )
    parser.add_argument("--api-key", help="Verkada API Key.", required=True)
    parser.add_argument("--token", help="ParkPow Token.", required=True)
    parser.add_argument("--pp-url", help="ParkPow Server URL.", required=False)

    args = parser.parse_args()

    webhook_queue = WebhookQueue(args.api_key, args.token, args.pp_url)
    monitor = threading.Thread(target=webhook_queue.process, args=())
    server_thread = threading.Thread(target=server_worker, args=(webhook_queue,))
    monitor.start()
    server_thread.start()
