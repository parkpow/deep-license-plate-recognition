import sys
from io import BytesIO
from typing import Any, Dict, Union

import requests


class WebhookError(Exception):
    """Raised when a webhook response does not return 200 status."""


def get_webhook_payload(url: str) -> Dict[str, Any]:
    """Return a sample payload to the request."""
    return {
        "json": {
            "hook": {
                "target": url,
                "id": "camera-1",
                "event": "recognition",
                "filename": (
                    "camera-1_screenshots/21-10-27/06-20-55.161444.jpg"
                ),
            },
            "data": {
                "camera_id": "camera-1",
                "filename": (
                    "camera-1_screenshots/21-10-27/06-20-55.161444.jpg"
                ),
                "timestamp": "2021-10-27T06:20:55.161444Z",
                "timestamp_local": "2021-10-27 06:20:55.161444 00:00",
                "results": [
                    {
                        "box": {"xmin": 153,
                                "ymin": 91,
                                "xmax": 302,
                                "ymax": 125},
                        "plate": "slz9043m",
                        "region": {"code": "it", "score": 0.476},
                        "score": 0.906,
                        "candidates": [
                            {"plate": "slz9043m"},
                            {"plate": "slz9043m"},
                            {"plate": "slz9043m"},
                        ],
                        "dscore": 0.641,
                        "vehicle": {
                            "score": 0.254,
                            "type": "SUV",
                            "box": {"xmin": 603,
                                    "ymin": 0,
                                    "xmax": 1099,
                                    "ymax": 174},
                        },
                        "model_make": [
                            {"make": "Mercedes-Benz",
                             "model": "Citan",
                             "score": 0.075},
                            {"make": "Mercedes-Benz",
                             "model": "GLC",
                             "score": 0.07},
                            {"make": "Mercedes-Benz",
                             "model": "GLS",
                             "score": 0.061},
                        ],
                        "color": [
                            {"color": "white", "score": 0.889},
                            {"color": "silver", "score": 0.027},
                            {"color": "brown", "score": 0.013},
                        ],
                        "orientation": [
                            {"orientation": "Front", "score": 0.943},
                            {"orientation": "Unknown", "score": 0.031},
                            {"orientation": "Rear", "score": 0.026},
                        ],
                        "direction": 210,
                        "source_url": "/user-data/Elixirtech_Slow2_Indoor.mp4",
                        "position_sec": 23.47,
                    }
                ],
            },
        }
    }


def get_files_payload() -> Dict[str, Any]:
    """Return a request payload containing files."""
    url = (
        "https://platerecognizer.com/wp-content/uploads/2020/07/"
        "ALPR-license-plate-reader-images-API.jpg"
    )
    response = send_request(url)
    return {"upload": {"name": BytesIO(response.content)}}


def send_request(url: str,
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
    try:
        response = requests.post(url,
                                 data=data or {},
                                 files=files or {},
                                 timeout=30)
    except requests.exceptions.Timeout:
        raise WebhookError("The request timed out.")
    except requests.exceptions.TooManyRedirects:
        raise WebhookError(
            "The given URL might be misconfigured. "
            "Try a different one."
        )
    except requests.exceptions.RequestException as request_exception:
        raise WebhookError(str(request_exception)) from request_exception

    return response


def test_webhook() -> None:
    """Used to test the webhook."""
    url = sys.argv[1]
    payload = get_webhook_payload(url)
    files = get_files_payload()
    response = send_request(url, payload, files)
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.content}")

    if response.status_code >= 300:
        raise WebhookError(response.content)


if __name__ == "__main__":
    test_webhook()
