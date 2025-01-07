import logging
import time

import requests

lgr = logging.getLogger(__name__)

API_BASE = "https://api.platerecognizer.com"


class SnapshotApiError(Exception):
    status_code = 400


class LicenseVerificationError(SnapshotApiError):
    status_code = 403


class PayloadTooLargeError(SnapshotApiError):
    status_code = 413


class TooManyRequestsError(SnapshotApiError):
    status_code = 429


RETRY_LIMIT = 10


class Snapshot:
    def __init__(self, token, sdk_url=None):
        self.sdk_url = sdk_url
        if token is None:
            raise Exception("A TOKEN is required if using Cloud API")
        else:
            self.session = requests.Session()
            self.session.headers = {"Authorization": "Token " + token}

    def recognition(self, data: dict):
        """
        Send image b64 to Snapshot

        :param data:
        :return:
        """
        if self.sdk_url:
            api_base = self.sdk_url
        else:
            api_base = API_BASE

        url = f"{api_base}/v1/plate-reader/"
        lgr.debug(f"Url: {url}")
        tries = 1
        while True:
            # files = dict(upload=image_b64)
            response = self.session.post(url, data)
            lgr.debug(f"Plate Recognition Response: {response} -----------------")
            lgr.debug(response.text)
            lgr.debug("End Plate Recognition Response -----------------")
            if response.status_code < 200 or response.status_code > 300:
                if response.status_code == 429:
                    time.sleep(1)
                    tries += 1
                    if tries > RETRY_LIMIT:
                        raise TooManyRequestsError(response.json()["detail"])
                elif response.status_code == 403:
                    raise LicenseVerificationError(response.json()["detail"])
                elif response.status_code == 413:
                    raise PayloadTooLargeError(response.json()["error"])
                elif response.status_code == 400:
                    raise SnapshotApiError(response.json())
                else:
                    response.raise_for_status()
            else:
                res_json = response.json()
                if "error" in res_json:
                    raise SnapshotApiError(res_json["error"])

                return res_json


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

    def log_vehicle(self, data):
        endpoint = "log-vehicle/"
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
