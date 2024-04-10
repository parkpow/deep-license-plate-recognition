import argparse
import base64
import cgi
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
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


class VerkadaApi:
    def __init__(
        self,
        api_key,
    ):
        self.api_key = api_key

    @staticmethod
    def download_image(url):
        """
        Download Plate Image from URL
        """
        try:
            res = requests.get(url)
            if res.status_code == 200:
                return base64.b64encode(res.content).decode("utf-8")
            else:
                lgr.debug(f"download_image res: {res}")
        except Exception as e:
            lgr.error("error", exc_info=e)

    def get_seen_license_plate_image(self, camera_id, timestamp, plate):
        """
        Returns the timestamps, detected license plate numbers, and images of all license plates seen by a camera.
        :param camera_id:
        :param timestamp:
        :param plate:
        :return:
        """
        params = {
            "page_size": 5,
            "camera_id": camera_id,
            "license_plate": plate,
            "start_time": timestamp - 1,
            "end_time": timestamp + 1,
        }
        url = "https://api.verkada.com/cameras/v1/analytics/lpr/images"
        headers = {"accept": "application/json", "x-api-key": self.api_key}
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                for detection in data["detections"]:
                    if (
                        detection["timestamp"] == timestamp
                        and detection["license_plate"] == plate
                    ):
                        return VerkadaApi.download_image(detection["image_url"])
            else:
                lgr.error(f"{response.text}")
        except Exception as e:
            lgr.error("error", exc_info=e)


class ParkPowApi:
    def __init__(self, token, sdk_url=None):
        if token is None:
            raise Exception("ParkPow TOKEN is required if using Cloud API")
        if sdk_url:
            self.api_base = sdk_url + "/api/v1/"
        else:
            self.api_base = "https://app.parkpow.com/api/v1/"

        lgr.debug(f"Api Base: {self.api_base}")
        self.session = requests.Session()
        self.session.headers = {"Authorization": "Token " + token}

    def log_vehicle(
        self, encoded_image, license_plate_number, confidence, camera, timestamp
    ):
        endpoint = "log-vehicle/"
        p_time = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f%z")
        data = {
            "camera": camera,
            "image": encoded_image,
            "results": [
                {
                    "plate": license_plate_number,
                    "score": confidence,
                    "box": {"xmin": 0, "ymin": 0, "ymax": 0, "xmax": 0},
                }
            ],
            "time": p_time,
        }
        try:
            while True:
                response = self.session.post(self.api_base + endpoint, json=data)
                lgr.debug(f"response: {response}")
                if response.status_code < 200 or response.status_code > 300:
                    if response.status_code == 429:
                        time.sleep(1)
                    else:
                        lgr.error(response.text)
                        raise Exception("Error logging vehicle")
                else:
                    res_json = response.json()
                    return res_json
        except requests.RequestException as e:
            lgr.error("Error", exc_info=e)


class WebhookQueue:
    def __init__(self, api_key, token, pp_url, max_workers=4):
        self.verkada = VerkadaApi(api_key)
        self.parkpow = ParkPowApi(token, pp_url)

        self.queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def enqueue(self, message):
        self.queue.put(message)

    def process(self):
        while True:
            data = self.queue.get()
            lgr.info(f"Processing message: {data}")

            camera_id = data["camera_id"]
            created_at = data["created"]
            confidence = data["confidence"]
            license_plate_number = data["license_plate_number"]

            image = self.verkada.get_seen_license_plate_image(
                camera_id, created_at, license_plate_number
            )
            if image is not None:
                self.parkpow.log_vehicle(
                    image, license_plate_number, confidence, camera_id, created_at
                )


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
        Endpoint has 2 seconds to respond to a notification. Otherwise,
        the notification is treated as failed and will be retried only once.
        :return:
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
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


def test(ns):
    """
    Test API calls without webhook server
    :param ns:
    :return:
    """
    camera_id, timestamp, plate, confidence = ns.test.split(",")
    ts = int(timestamp)
    v = VerkadaApi(ns.api_key)
    img = v.get_seen_license_plate_image(camera_id, ts, plate)
    if img is not None:
        pp = ParkPowApi(ns.token, ns.pp_url)
        pp.log_vehicle(img, plate, confidence, camera_id, ts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Forward Verkada LPR Webhook Events to ParkPow."
    )
    parser.add_argument("--api-key", help="Verkada API Key.", required=True)
    parser.add_argument("--token", help="ParkPow Token.", required=True)
    parser.add_argument("--pp-url", help="ParkPow Server URL.", required=False)
    parser.add_argument(
        "--test",
        help="Sample Comma separated Camera ID, Timestamp, Plate and Confidence.",
        required=False,
    )

    args = parser.parse_args()
    if args.test:
        test(args)
    else:
        webhook_queue = WebhookQueue(args.api_key, args.token, args.pp_url)
        monitor = threading.Thread(target=webhook_queue.process, args=())
        server_thread = threading.Thread(target=server_worker, args=(webhook_queue,))
        monitor.start()
        server_thread.start()
