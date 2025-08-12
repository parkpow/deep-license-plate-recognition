import argparse
import json
import os
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import requests


class WebhookError(Exception):
    """Raised when a webhook response does not return 200 status."""


class WebhookTester:
    """Main class to use in testing the webhook."""

    def __init__(
        self,
        url: str,
        token: str | None = None,
        camera_id: str | None = None,
        plate: str | None = None,
        region_code: str | None = None,
        timestamp: str | None = None,
    ):
        self.url = url or os.environ.get("URL", "")
        if not self.url:
            raise ValueError("Set URL environment variable when running docker.")
        self.token = token or os.environ.get("TOKEN")
        self.camera_id = camera_id or os.environ.get("CAMERA", "camera-1")
        self.plate = plate or os.environ.get("PLATE", "pl8rec")
        self.region_code = region_code or os.environ.get("REGION", "us-ca")
        self.timestamp = timestamp or os.environ.get(
            "TIMESTAMP", datetime.now(timezone.utc).isoformat()
        )

    def get_webhook_payload(self) -> dict[str, Any]:
        """Return a sample payload to the request."""
        return {
            "json": json.dumps(
                {
                    "hook": {
                        "target": self.url,
                        "id": self.camera_id,
                        "event": "recognition",
                        "filename": (f"{self.camera_id}_screenshots/image.jpg"),
                    },
                    "data": {
                        "camera_id": self.camera_id,
                        "filename": (f"{self.camera_id}_screenshots/image.jpg"),
                        "timestamp": self.timestamp,
                        "timestamp_local": self.timestamp,
                        "results": [
                            {
                                "box": {
                                    "xmax": 412,
                                    "xmin": 337,
                                    "ymax": 305,
                                    "ymin": 270,
                                },
                                "candidates": [
                                    {"plate": self.plate, "score": 0.902},
                                    {"plate": "plbrec", "score": 0.758},
                                ],
                                "color": [
                                    {"color": "red", "score": 0.699},
                                    {"color": "black", "score": 0.134},
                                    {"color": "blue", "score": 0.03},
                                ],
                                "dscore": 0.757,
                                "model_make": [
                                    {"make": "Porsche", "model": "911", "score": 0.43},
                                    {
                                        "make": "Porsche",
                                        "model": "Carrera",
                                        "score": 0.2,
                                    },
                                    {
                                        "make": "Porsche",
                                        "model": "Carrera GTS",
                                        "score": 0.07,
                                    },
                                ],
                                "orientation": [
                                    {"orientation": "Rear", "score": 0.883},
                                    {"orientation": "Front", "score": 0.07},
                                    {"orientation": "Unknown", "score": 0.047},
                                ],
                                "plate": self.plate,
                                "region": {"code": self.region_code, "score": 0.179},
                                "score": 0.902,
                                "vehicle": {
                                    "box": {
                                        "xmax": 590,
                                        "xmin": 155,
                                        "ymax": 373,
                                        "ymin": 71,
                                    },
                                    "score": 0.709,
                                    "type": "Sedan",
                                },
                                "direction": 210,
                                "source_url": ("/user-data/video.mp4"),
                                "position_sec": 23.47,
                            }
                        ],
                    },
                }
            )  # end of json.dumps
        }

    def get_files_payload(self) -> dict[str, Any]:
        """Return a request payload containing files."""
        url = (
            "https://platerecognizer.com/wp-content/uploads/2020/07/"
            "ALPR-license-plate-reader-images-API.jpg"
        )
        response = self.send_request("get", url)
        print(f"This request includes a {len(response.content)/ 1024:.1f} KB image.")
        return {"upload": ("image.jpg", BytesIO(response.content))}

    def send_request(
        self,
        method: str,
        url: str,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
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
            raise ValueError("Method not supported. Only accepts `get` or `post`.")
        headers = {}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        try:
            response = getattr(requests, method.lower())(
                url, data=data, files=files, timeout=30, headers=headers
            )
        except requests.exceptions.Timeout as exc:
            raise WebhookError("The request timed out.") from exc
        except requests.exceptions.TooManyRedirects as exc:
            raise WebhookError(
                "The given URL might be misconfigured. " "Try a different one."
            ) from exc
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
            print(f"--> Invalid status code: {response.status_code}")
            raise WebhookError(content)
        else:
            print(f"Status code: {response.status_code}")
            print(f"Response content: {content}")
            print("--> The server successfully received the webhook.")

    @staticmethod
    def parse_args():
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="Test webhook with license plate recognition data"
        )
        parser.add_argument("--url", help="Webhook URL to test")
        parser.add_argument("--token", help="Header authorization token")
        parser.add_argument("--camera-id", help="Camera ID (default: camera-1)")
        parser.add_argument("--plate", help="License plate text (default: pl8rec)")
        parser.add_argument("--region", help="Region code (default: us-ca)")
        parser.add_argument(
            "--timestamp",
            help="Timestamp (default: current UTC time). Format: 2025-08-11T16:42:58.740143Z",
        )
        return parser.parse_args()


if __name__ == "__main__":
    args = WebhookTester.parse_args()
    try:
        tester = WebhookTester(
            url=args.url,
            token=args.token,
            camera_id=args.camera_id,
            plate=args.plate,
            region_code=args.region,
            timestamp=args.timestamp,
        )
        tester.execute()
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print("--> An error occurred:")
        print(e)
        print("--> The webhook failed.")
