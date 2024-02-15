import argparse
import ast
import base64
import csv
import datetime
import json
import logging
import os
import sys
import time
from pathlib import Path

import requests
from configobj import ConfigObj

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(levelname)-5s  [%(name)s.%(lineno)d] => %(message)s",
)

lgr = logging.getLogger("upload-csv")

STREAM_DIR = Path(os.environ.get("STREAM_DIR", "/user-data/"))
CAMERA_TOKEN = "$(camera)"


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

    def log_vehicle_api(self, data):
        endpoint = "log-vehicle/"
        try:
            while True:
                response = self.session.post(self.api_base + endpoint, json=data)
                lgr.debug(f"response: {response}")
                if response.status_code < 200 or response.status_code > 300:
                    if response.status_code == 429:
                        time.sleep(1)
                    else:
                        logging.error(response.text)
                        raise Exception("Error logging vehicle")
                else:
                    res_json = response.json()
                    return res_json
        except requests.RequestException as e:
            lgr.error("Error", exc_info=e)

    def is_duplicate(self, ts_datetime: datetime.datetime, plate, camera_id):
        """
        Check parkpow visit within ts_datetime +1 second
        :param ts_datetime:
        :param plate:
        :param camera_id:
        :return:
        """
        endpoint = "visit-list/"
        pp_date_format = "%Y-%m-%dT%H:%M:%S"
        start = ts_datetime.strftime(pp_date_format)
        end = (ts_datetime + datetime.timedelta(seconds=1)).strftime(pp_date_format)
        params = dict(
            plate=plate,
            # camera=camera_id,
            start=start,
            end=end,
        )
        lgr.debug(f"Checking parkpow visits Params: {params}")
        try:
            response = self.session.get(self.api_base + endpoint, params=params)
            lgr.debug(f"Response : {response}")
            if response.status_code < 200 or response.status_code > 300:
                if response.status_code == 429:
                    time.sleep(1)
                else:
                    lgr.error(response.text)
                    raise Exception(f"Error logging vehicle: {response}")
            else:
                response = response.json()
                lgr.debug(f"Visits: {response}")
                if response["estimated_count"] > 0 and response["results"]:
                    for visit in response["results"]:
                        lgr.debug(f"Visit: {json.dumps(visit)}")
                        # start_data = visit["start_data"]
                        vp = visit["vehicle"]["license_plate"]
                        v_cam = visit["start_cam"]["code"]
                        if vp == plate and v_cam == camera_id:
                            return True

            return False
        except requests.RequestException as e:
            lgr.error("Error", exc_info=e)


def parse_row_result(row: list):
    if len(row) == 7:
        lgr.debug("mode=vehicle")
        # mmc=true mode=vehicle
        # timestamp,file,source_url,position_sec,direction,plate,vehicle
        file = row[1]
        plate = ast.literal_eval(row[5])
        position_sec = row[3]
        if len(row[4]):
            direction = row[4]
        else:
            direction = None
        vehicle = ast.literal_eval(row[6])

        # if plate["props"] is None: # TODO how to handle such a case

    else:
        lgr.debug("mode=plate")
        # timestamp,plate,score,dscore,file,box,model_make,color,vehicle,region,orientation,
        # candidates,source_url,position_sec,direction
        file = row[4]
        position_sec = row[13]
        if len(row[14]):
            direction = row[14]
        else:
            direction = None
        region = ast.literal_eval(row[9])
        plate = {
            "box": ast.literal_eval(row[5]),
            "score": row[3],
            "type": "Plate",
            "props": {
                "plate": [{"value": row[1], "score": row[2]}],
                "region": [{"value": region["code"], "score": region["score"]}],
            },
        }

        vehicle = ast.literal_eval(row[8])
        vehicle["props"] = {}
        if len(row[7]):
            colors = ast.literal_eval(row[7])
            pp_colors = []
            for color in colors:
                pp_colors.append({"value": color["color"], "score": color["score"]})
            vehicle["props"]["color"] = pp_colors
        else:
            vehicle["props"]["color"] = []

        if len(row[10]):
            orientations = ast.literal_eval(row[10])
            pp_orientations = []
            for orientation in orientations:
                pp_orientations.append(
                    {"value": orientation["orientation"], "score": orientation["score"]}
                )
            vehicle["props"]["orientation"] = pp_orientations
        else:
            vehicle["props"]["orientation"] = []

        if len(row[6]):
            vehicle["props"]["make_model"] = ast.literal_eval(row[6])
        else:
            vehicle["props"]["make_model"] = []

    result = {
        "plate": plate,
        "direction": direction,
        "position_sec": position_sec,
        "vehicle": vehicle,
    }
    timestamp = row[0]
    return timestamp, file, result


def row_payload(result: dict, screenshot, timestamp, camera_id):
    screenshot = screenshot.lstrip("/")
    screenshot_path = STREAM_DIR / screenshot
    lgr.debug(f"screenshot Path: {screenshot_path}")
    if screenshot_path.exists():
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    else:
        raise Exception(f"Screenshot not found: {screenshot}")

    d = {
        "camera": camera_id,
        "image": encoded_image,
        "results": [result],
        "time": timestamp,
    }

    return d


def parse_camera(config, camera_id):
    """
    Parse a camera config into:
    {
        'id': '<camera-id>',
        'image_format': '',
        'csv_file': '',
        'webhooks': ['webhook1', 'webhook2' ]
    }
    :param camera_id:
    :param config:
    :return:
    """
    lgr.debug(f"Config: {config}")
    camera_config = {"id": camera_id, "webhooks": []}
    if "webhook_targets" in config:
        webhook_targets = config["webhook_targets"]
        lgr.debug(f"webhook_targets: {webhook_targets}")
        if type(webhook_targets) is list:
            camera_config["webhooks"] = webhook_targets
        elif type(webhook_targets) is str:
            if "http://" in webhook_targets or "https://" in webhook_targets:
                raise Exception(
                    "Unsupported webhook format. Update to match "
                    "https://guides.platerecognizer.com/docs/parkpow/integrations#step-2-update-stream"
                    "-configini"
                )
            camera_config["webhooks"] = [webhook_targets]
    else:
        lgr.debug("No webhook targets")

    if "csv_file" in config:
        camera_config["csv_file"] = config["csv_file"]

    if "image_format" in config:
        camera_config["image_format"] = config["image_format"]

    return camera_config


def format_path(camera, date_obj, s):
    return date_obj.strftime(s.replace(CAMERA_TOKEN, camera))


def select_camera_id(ts_datetime, camera_webhooks, path):
    # Get camera ID from file or csv filename
    lgr.debug(f"datetime_obj: {ts_datetime}")
    for key, value in camera_webhooks.items():
        csv_path = format_path(key, ts_datetime, value["csv_file"])
        lgr.debug(f"Key: {key} csv_path: {csv_path}")

        if STREAM_DIR / csv_path == path:
            return key
    raise Exception(f"Unable to select a camera ID from: {path}")


def slice_image(data, n=20):
    """
    For logging purposes
    :param n:
    :param data:
    :return:
    """
    dict2 = dict(data)
    dict2["image"] = dict2["image"][:n]
    return dict2


def parse_parkpow_webhooks(config):
    """
    Get ParkPow webhooks from config
    :param config:
    :return:
    """
    parkpow_webhooks = {}
    webhooks_config = config["webhooks"]
    for webhook_id in webhooks_config.sections:
        webhook_config = webhooks_config[webhook_id]
        url = webhook_config["url"]
        lgr.debug(f"Webhook URL: {url}")

        parkpow_webhook_endpoint = "/api/v1/webhook-receiver"
        if parkpow_webhook_endpoint in url:
            url = url.split(parkpow_webhook_endpoint)[0]
            header = webhook_config["header"]
            lgr.debug(f"Header: {header}")
            parkpow_webhooks[webhook_id] = {
                "url": url,
                "token": header.split("Token ")[1],
            }
    return parkpow_webhooks


def parse_camera_webhooks(config, parkpow_webhooks):
    """
    Get cameras with ParkPow webhook
    :param config:
    :param parkpow_webhooks:
    :return:
    """
    camera_webhooks = {}
    cameras = config["cameras"]
    # Fallback to image_format when csv filename has no camera token
    #  i.e CAMERA_TOKEN not in cameras_image_format
    #  also check camera image_format set per camera
    # if "image_format" in cameras:
    #     cameras_image_format = cameras["image_format"]
    # else:
    #     cameras_image_format = "$(camera)_screenshots/%y-%m-%d/%H-%M-%S.%f.jpg"
    # lgr.info(f"cameras_image_format: {cameras_image_format}")

    camera_ids = cameras.sections
    for camera_id in camera_ids:
        lgr.debug(f"camera ID: {camera_id}")
        camera_config = cameras[camera_id]
        config = parse_camera(camera_config, camera_id)
        lgr.debug(f"config: {config}")
        # Camera webhooks that are ParkPow webhooks
        camera_parkpow_hooks = []
        for cam_webhook in config["webhooks"]:
            if cam_webhook in parkpow_webhooks:
                camera_parkpow_hooks.append(cam_webhook)

        if any(camera_parkpow_hooks):
            camera_webhooks[camera_id] = config
            camera_webhooks[camera_id]["webhooks"] = camera_parkpow_hooks
        else:
            lgr.debug(f"Camera {camera_id} does not have a parkpow webhook")
    return camera_webhooks


def upload_row_result(selected_camera, parkpow_webhooks, data, de_duplicate, dt):
    for webhook_id in selected_camera["webhooks"]:
        lgr.debug(f"Sending to ParkPow webhook: {webhook_id}")
        parkpow_webhook = parkpow_webhooks[webhook_id]
        parkpow = ParkPowApi(parkpow_webhook["token"], parkpow_webhook["url"])
        plate = data["results"][0]["plate"]
        if plate["props"] is None:
            plate_number = "NONE"  # TODO how to handle such a case
        else:
            plate_number = plate["props"]["plate"][0]["value"]

        if de_duplicate and parkpow.is_duplicate(
            dt, plate_number, selected_camera["id"]
        ):
            lgr.info("Skipped duplicate")
            continue

        lgr.debug(f"data: {slice_image(data)}")
        vehicle_log = parkpow.log_vehicle_api(data)
        lgr.info(f"vehicle_log: {vehicle_log}")


def main(args):
    """
    Iterate CSV files in a directory and upload
    - Upload CSV rows and images to ParkPow
    - Prevent duplicates, skip uploaded
    - Support Reading Stream Config for ParkPow Configs
    """
    config_file = STREAM_DIR / "config.ini"
    if not config_file.exists():
        lgr.error("config.ini not found.")
        exit(1)

    with open(config_file) as config_file_p:
        config = ConfigObj(config_file_p)

    parkpow_webhooks = parse_parkpow_webhooks(config)
    lgr.debug(f"ParkPow WebHooks: {parkpow_webhooks}")

    camera_webhooks = parse_camera_webhooks(config, parkpow_webhooks)
    lgr.info(f"camera_webhooks: {camera_webhooks}")

    if not camera_webhooks:
        lgr.error("No camera configured with a ParkPow webhook found in the config.ini")
        return

    # Selecting camera ID from CSV requires it to have been used in output
    for key, value in camera_webhooks.items():
        if CAMERA_TOKEN not in value["csv_file"]:
            lgr.error(
                f"Will be unable to trace camera ID for {key}, Add $(camera) in csv_file config."
            )
            return

    for path in STREAM_DIR.glob("**/*.csv"):
        lgr.info(f"Processing CSV: {path}")
        with open(path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            selected_camera = None
            for row in reader:
                lgr.debug(f"Row: {row}")
                if row[0] == "timestamp":
                    lgr.debug("Skipped header row")
                    continue

                timestamp, file, result = parse_row_result(row)
                lgr.info(f"Processing: {timestamp} - File: {file}")
                lgr.debug(f"Result: {json.dumps(result)}")
                ts_datetime = datetime.datetime.strptime(
                    timestamp, "%Y-%m-%d %H:%M:%S.%f%z"
                )

                if selected_camera is None:
                    selected_camera_id = select_camera_id(
                        ts_datetime, camera_webhooks, path
                    )
                    selected_camera = camera_webhooks[selected_camera_id]

                lgr.debug(f"selected_camera: {selected_camera}")

                data = row_payload(result, file, timestamp, selected_camera_id)

                upload_row_result(
                    selected_camera,
                    parkpow_webhooks,
                    data,
                    args.de_duplicate,
                    ts_datetime,
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload CSV rows and images to ParkPow",
        epilog="",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--de-duplicate",
        help="Skip duplicates by comparing plate and timestamp.",
        type=bool,
        default=True,
        required=False,
    )

    main(parser.parse_args())
