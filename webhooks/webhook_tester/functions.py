import json
from io import BytesIO
from typing import Any, Dict, Union

import requests


class WebhookError(Exception):
    """Raised when a webhook response does not return 200 status."""


class WebhookTester:
    """Main class to use in testing the webhook."""

    def __init__(self, url: str):
        self.url = url

    def get_webhook_payload(self) -> Dict[str, Any]:
        """Return a sample payload to the request."""
        return {
            "json":
            json.dumps({
                "hook": {
                    "target": self.url,
                    "id": "camera-1",
                    "event": "recognition",
                    "filename": ("camera-1_screenshots/image.jpg"),
                },
                "data": {
                    "camera_id":
                    "camera-1",
                    "filename": ("camera-1_screenshots/image.jpg"),
                    "timestamp":
                    "2021-10-27T06:20:55.161444Z",
                    "timestamp_local":
                    "2021-10-27 06:20:55.161444 00:00",
                    "results": [{
                        "box": {
                            "xmax": 412,
                            "xmin": 337,
                            "ymax": 305,
                            "ymin": 270
                        },
                        "candidates": [{
                            "plate": "pl8rec",
                            "score": 0.902
                        }, {
                            "plate": "plbrec",
                            "score": 0.758
                        }],
                        "color": [{
                            "color": "red",
                            "score": 0.699
                        }, {
                            "color": "black",
                            "score": 0.134
                        }, {
                            "color": "blue",
                            "score": 0.03
                        }],
                        "dscore":
                        0.757,
                        "model_make": [{
                            "make": "Porsche",
                            "model": "911",
                            "score": 0.43
                        }, {
                            "make": "Porsche",
                            "model": "Carrera",
                            "score": 0.2
                        }, {
                            "make": "Porsche",
                            "model": "Carrera GTS",
                            "score": 0.07
                        }],
                        "orientation": [{
                            "orientation": "Rear",
                            "score": 0.883
                        }, {
                            "orientation": "Front",
                            "score": 0.07
                        }, {
                            "orientation": "Unknown",
                            "score": 0.047
                        }],
                        "plate":
                        "pl8rec",
                        "region": {
                            "code": "us-ca",
                            "score": 0.179
                        },
                        "score":
                        0.902,
                        "vehicle": {
                            "box": {
                                "xmax": 590,
                                "xmin": 155,
                                "ymax": 373,
                                "ymin": 71
                            },
                            "score": 0.709,
                            "type": "Sedan"
                        },
                        "direction":
                        210,
                        "source_url": ("/user-data/video.mp4"),
                        "position_sec":
                        23.47,
                    }],
                },
            })  # end of json.dumps
        }

    def get_files_payload(self) -> Dict[str, Any]:
        """Return a request payload containing files."""
        url = ("https://platerecognizer.com/wp-content/uploads/2020/07/"
               "ALPR-license-plate-reader-images-API.jpg")
        response = self.send_request("get", url)
        print(f'This request includes a {len(response.content)/ 1024:.1f} KB image.')
        return {"upload": ("image.jpg", BytesIO(response.content))}

    @staticmethod
    def send_request(
            method: str,
            url: str,
            data: Union[Dict[str, Any], None] = None,
            files: Union[Dict[str, Any], None] = None,
    ) -> requests.Response:
        """
        Send the actual request to the given URL along with the parameters.

        Args:
            url (str): The target URL.
            data (Union[Dict[str, Any], None]): Payload to send to the URL.
            files (Union[Dict[str, Any], None]): Files to send to the URL.

        Returns:
            requests.Response: The Response object.
        """
        if method.lower() not in ["get", "post"]:
            raise ValueError(
                "Method not supported. Only accepts `get` or `post`.")

        try:
            response = getattr(requests, method.lower())(url,
                                                         data=data,
                                                         files=files,
                                                         timeout=30)
        except requests.exceptions.Timeout:
            raise WebhookError("The request timed out.")
        except requests.exceptions.TooManyRedirects:
            raise WebhookError("The given URL might be misconfigured. "
                               "Try a different one.")
        except requests.exceptions.RequestException as request_exception:
            raise WebhookError(str(request_exception)) from request_exception

        return response

    def execute(self) -> None:
        """Used to test the webhook."""
        print(f'{" Sending Webhook (JSON + Image) ":-^80s}')
        payload = self.get_webhook_payload()
        files = self.get_files_payload()
        response = self.send_request("post", self.url, payload, files)
        content = response.text
        if response.status_code >= 300:
            print(f'--> Invalid status code: {response.status_code}')
            raise WebhookError(content)
        else:
            print(f"Status code: {response.status_code}")
            print(f"Response content: {content}")
            print('--> The server successfully received the webhook.')
