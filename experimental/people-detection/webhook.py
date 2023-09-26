import json
import logging
from io import BytesIO

import cv2
import requests

lgr = logging.getLogger(__name__)


class WebhookError(Exception):
    """Raised when a webhook response does not return 200 status."""


class WebhookSender:
    """Main class to use in sending the webhook."""

    def __init__(self, url: str):
        self.url = url

    def get_webhook_payload(self, data):
        """Return a sample payload to the request."""
        payload_results = []
        for result in data["results"]:
            xy_xy = result["xy_xy"]
            payload_result = {
                "box": {
                    "xmin": xy_xy[0],
                    "ymin": xy_xy[1],
                    "ymax": xy_xy[2],
                    "xmax": xy_xy[3],
                },
                "type": result["class"],
                "score": result["confidence"],
            }
            payload_results.append(payload_result)

        return {
            "json": json.dumps(
                {
                    "hook": {"target": self.url, "id": 2, "event": "image.done"},
                    "data": {
                        "processing_time": data["processing_time"],
                        "timestamp": data["timestamp"],
                        "results": payload_results,
                        "filename": "image.jpeg",
                        "version": 1,
                        "camera_id": None,
                    },
                }
            )
        }

    def get_file_payload(self, cv2_image):
        """Return a request payload containing files."""
        image_bytes = cv2.imencode(".jpg", cv2_image)[1].tobytes()
        return {"upload": ("image.jpg", BytesIO(image_bytes))}

    @staticmethod
    def send_request(
        method,
        url,
        data=None,
        files=None,
    ):
        """
        Send the actual request to the given URL along with the parameters.

        Args:
            url (str): The target URL.
            data (Union[Dict[str, Any], None]): Payload to send to the URL.
            files (Union[Dict[str, Any], None]): Files to send to the URL.

        Returns:
            requests.Response: The Response object.
            :param files:
            :param data:
            :param url:
            :param method:
        """
        if method.lower() not in ["get", "post"]:
            raise ValueError("Method not supported. Only accepts `get` or `post`.")

        try:
            response = getattr(requests, method.lower())(
                url, data=data, files=files, timeout=30
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

    def execute(self, cv2_image, data):
        """Used to send the webhook."""
        lgr.info(f'{" Sending Webhook (JSON + Image) ":-^80s}')
        payload = self.get_webhook_payload(data)
        if cv2_image is None:
            file = None
        else:
            file = self.get_file_payload(cv2_image)
        response = self.send_request("post", self.url, payload, file)
        content = response.text
        if response.status_code >= 300:
            lgr.info(f"Invalid status code: {response.status_code}")
            raise WebhookError(content)
        else:
            lgr.info(f"Status code: {response.status_code}")
            lgr.info(f"Response content: {content}")
            lgr.info("The server successfully received the webhook.")
