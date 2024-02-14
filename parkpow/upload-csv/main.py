import argparse
import base64
import csv
import datetime
import logging
import os
import sys
import time
from pathlib import Path
import json
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

STREAM_DIR = Path("/user-data/")
CAMERA_TOKEN = '$(camera)'


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

    def is_duplicate(self, timestamp, plate, camera_id):

        # https://app.parkpow.com/api/v1/visit-list/
        lgr.debug(f'checking parkpow visits since {timestamp}')
        try:
            response = self.session.get(
                "https://app.parkpow.com/api/v1/visit-list/",
                params=dict(
                    plate=plate, start=timestamp, camera=camera_id
                ),

            )

            lgr.debug(response.text)
            response = response.json()

            if response['estimated_count'] > 0 and response['results']:
                visit = response['results'][0]
                start_data = visit['start_data']

                # Assert Plate
                assert visit['vehicle']['license_plate'] == plate
                assert start_data['plate'] == plate

                # Assert Regions
                # assert start_data['region']['code'] == REGIONS[0]

                # Assert CameraId
                assert visit['start_cam']['code'] == camera_id

                # Assert MMC
                assert start_data['color'][0]['color'] == 'black'
                # Warning: new MMC does not include this model.
                # assert start_data['model_make'][0]['make'] == 'Riley'
                # assert start_data['model_make'][0]['model'] == 'RMF'

            return False
        except Exception as e:
            lgr.error(e)
            exit(1)
        return False


def parse_row_result(row: list):
    x = {
        "plate": {
            "box": {
                "xmin": 231,
                "ymin": 238,
                "ymax": 266,
                "xmax": 305
            },
            "score": 0.592,
            "type": "Plate",
            "props": {
                "plate": [
                    {
                        "value": "smm1439",
                        "score": 0.905
                    },
                    {
                        "value": "smh1439",
                        "score": 0.743
                    }
                ],
                "region": [
                    {
                        "value": "bg",
                        "score": 0.795
                    }
                ]
            }
        },
        "direction": 180,
        "position_sec": 34.94,
        "vehicle": {
            "box": {
                "xmin": 231,
                "ymin": 131,
                "ymax": 523,
                "xmax": 1070
            },
            "score": 0.834,
            "type": "Sedan",
            "props": {
                "color": [
                    {
                        "score": 0.877,
                        "value": "silver"
                    },
                    {
                        "score": 0.019,
                        "value": "black"
                    },
                    {
                        "score": 0.016,
                        "value": "green"
                    }
                ],
                "orientation": [
                    {
                        "score": 0.937,
                        "value": "Front"
                    },
                    {
                        "score": 0.032,
                        "value": "Rear"
                    },
                    {
                        "score": 0.031,
                        "value": "Unknown"
                    }
                ],
                "make_model": [
                    {
                        "make": "BMW",
                        "score": 0.55,
                        "model": "5 Series"
                    },
                    {
                        "make": "BMW",
                        "score": 0.153,
                        "model": "E83"
                    },
                    {
                        "make": "BMW",
                        "score": 0.029,
                        "model": "X5"
                    }
                ]
            }
        }
    }

    if len(row) == 7:
        # mmc=true mode=vehicle
        # timestamp,file,source_url,position_sec,direction,plate,vehicle
        file = row[1]
        plate = row[5]
        position_sec = row[3]
        direction = row[4]
        vehicle = row[6]

    else:
        # timestamp,plate,score,dscore,file,box,model_make,color,vehicle,region,orientation,
        # candidates,source_url,position_sec,direction
        file = row[4]
        plate_number = row[1]
        position_sec = row[13]
        direction = row[14]
        plate = {
            "box": json.loads(row[5]),
            "score": row[3],
            "type": "Plate",
            "props": {
                'plate': [
                    {
                        'value': plate_number,
                        'score' : row[2]
                    }
                ],
                'region': [

                ]
            }
        }

        vehicle = {
            "box": json.loads(row[8]),
            "score": 0.834,
            "type": "Sedan",
            "props": {

            }

        }

    result = {
        "plate": plate,
        "direction": direction,
        "position_sec": position_sec,
        "vehicle": vehicle
    }
    timestamp = row[0]

    return timestamp, file, plate, result


def row_payload(result: dict, screenshot: Path, timestamp, camera_id):
    screenshot_path = STREAM_DIR / screenshot
    lgr.debug(f"screenshot Path: {screenshot_path}")
    if screenshot_path.exists():
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    else:
        encoded_image = None
        raise Exception("encoded_image = None")

    d = {
        "camera": camera_id,
        "image": encoded_image,
        "results": [result],
        "time": timestamp,  # "2020-08-21T17:32"
    }

    return d


def process_camera(config):
    """
    Parse a camera config into:
    {
        'image_format': '',
        'csv_file': '',
        'webhooks': ['webhook1', 'webhook2' ]
    }
    :param config:
    :return:
    """
    lgr.debug(f"Config: {config}")
    camera_config = {"webhooks": []}
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


def select_camera_id(timestamp, camera_webhooks, path):
    # Get camera ID from file or csv filename
    datetime_obj = datetime.datetime.strptime(
        timestamp, "%Y-%m-%d %H:%M:%S.%f%z"
    )
    lgr.debug(f"datetime_obj: {datetime_obj}")
    for key, value in camera_webhooks.items():
        csv_path = format_path(key, datetime_obj, value['csv_file'])
        lgr.debug(f'Key: {key} csv_path: {csv_path}')

        if STREAM_DIR / csv_path == path:
            return key
    raise Exception('Unable to select a camera ID')


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
    lgr.debug(f"ParkPow WebHooks: {parkpow_webhooks}")

    camera_webhooks = {}

    cameras = config["cameras"]
    if "image_format" in cameras:
        cameras_image_format = cameras["image_format"]
    else:
        cameras_image_format = "$(camera)_screenshots/%y-%m-%d/%H-%M-%S.%f.jpg"

    camera_ids = cameras.sections
    for camera_id in camera_ids:
        lgr.debug(f"camera ID: {camera_id}")
        camera_config = cameras[camera_id]
        config = process_camera(camera_config)
        lgr.debug(f"config: {config}")
        # Camera webhooks that are ParkPow webhooks
        camera_parkpow_hooks = [
            cam_webhook
            for cam_webhook in config["webhooks"]
            if cam_webhook in parkpow_webhooks
        ]

        if any(camera_parkpow_hooks):
            camera_webhooks[camera_id] = config
            camera_webhooks[camera_id]["webhooks"] = camera_parkpow_hooks
        else:
            lgr.debug(f"Camera {camera_id} does not have a parkpow webhook")

    lgr.info(f"camera_webhooks: {camera_webhooks}")
    lgr.info(f"cameras_image_format: {cameras_image_format}")

    if not camera_webhooks:
        lgr.error("No camera configured with a ParkPow webhook found in the config.ini")
        return

    # Selecting camera ID from CSV requires it to have been used in output
    for key, value in camera_webhooks.items():
        if CAMERA_TOKEN not in value['csv_file'] and CAMERA_TOKEN not in cameras_image_format:
            # TODO check camera image_format override
            lgr.error(f"Will be unable to trace camera ID for {key}, Add $(camera) in image_format or csv_file config.")
            return

    for path in STREAM_DIR.glob("**/*.csv"):
        lgr.info(f'Processing CSV: {path}')
        with open(path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            selected_camera = None
            for row in reader:
                lgr.debug(f"Row: {row}")
                if row[0] == "timestamp":
                    lgr.debug("Skipped header row")
                    continue

                timestamp, file, plate, result = parse_row_result(row)
                lgr.info(f"Processing: {timestamp} - Plate: {plate} - File: {file}")

                if selected_camera is None:
                    selected_camera_id = select_camera_id(timestamp, camera_webhooks, path)
                    selected_camera = camera_webhooks[selected_camera_id]

                lgr.debug(f'selected_camera: {selected_camera}')

                for webhook_id in selected_camera['webhooks']:
                    parkpow_webhook = parkpow_webhooks[webhook_id]
                    parkpow = ParkPowApi(parkpow_webhook['token'], parkpow_webhook['url'])

                    if args.de_duplicate and parkpow.is_duplicate(timestamp, plate):
                        lgr.info(f'Skipped duplicate: {plate}')
                        continue

                    data = row_payload(result, file.lstrip("/"), timestamp, selected_camera_id)
                    lgr.debug(f"data: {data}")
                    vehicle_log = parkpow.log_vehicle_api(data)
                    lgr.info(f"vehicle_log: {vehicle_log}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload CSV rows and images to ParkPow",
        epilog="",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # parser.epilog = (
    #     "Examples:\n"
    #     "Upload CSV rows and images to ParkPow Cloud: "
    #     "./upload_csv.py --token <YOUR_API_TOKEN> --max-age 30 --api-url https://app.parkpow.com/api/v1/"
    #     "Upload CSV rows and images to ParkPow OnPremise: "
    #     "./upload_csv.py --token <YOUR_API_TOKEN> --max-age 30 --api-url http://local-or-public-IP:8000/api/v1/"
    # )
    # parser.add_argument(
    #     "-t",
    #     "--token",
    #     help="ParkPow API Token, refer to https://app.parkpow.com/account/token/",
    #     required=False,
    # )
    #
    parser.add_argument(
        "-d",
        "--de-duplicate",
        help="Skip duplicates by comparing plate and timestamp.",
        type=bool,
        default=True,
        required=False,
    )
    #
    # parser.add_argument(
    #     "-a",
    #     "--api-url",
    #     help="ParkPow API server URL. Example: http://local-or-public-IP:8000",
    #     required=False,
    # )

    # TODO parser.add_argument(
    #     "-c",
    #     "--camera-id",
    #     help="Camera ID",
    #     required=False,
    # )

    # parser.add_argument(
    #     "stream_dir",
    #     type=Path,
    #     help="Path to Stream directory",
    #     default=Path(''),
    #     required=False
    #
    # )
    main(parser.parse_args())
