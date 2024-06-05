import logging
import time

import requests

lgr = logging.getLogger(__name__)


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
        self,
        encoded_image,
        license_plate_number,
        confidence,
        camera,
        _datetime,
        plate_coordinates,
    ):
        endpoint = "log-vehicle/"
        p_time = _datetime.strftime("%Y-%m-%d %H:%M:%S.%f%z")
        data = {
            "camera": camera,
            "image": encoded_image,
            "results": [
                {
                    "plate": license_plate_number,
                    "score": confidence,
                    "box": {
                        "xmin": plate_coordinates[0],
                        "ymin": plate_coordinates[1],
                        "xmax": plate_coordinates[0] + plate_coordinates[2],
                        "ymax": plate_coordinates[1] + plate_coordinates[3],
                    },
                }
            ],
            "time": p_time,
        }
        try:
            tries = 0
            while tries < 5:
                response = self.session.post(self.api_base + endpoint, json=data)
                lgr.debug(f"response: {response}")
                if response.status_code < 200 or response.status_code > 300:
                    if response.status_code == 429:
                        tries += 1
                        time.sleep(1)
                    else:
                        lgr.error(response.text)
                        raise Exception("Error logging vehicle")
                else:
                    res_json = response.json()
                    return res_json
        except requests.RequestException as e:
            lgr.error("Error", exc_info=e)
            raise
