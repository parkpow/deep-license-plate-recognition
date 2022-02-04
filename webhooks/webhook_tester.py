import sys
from io import BytesIO

import requests
from PIL import Image


class WebhookError(Exception):
    """Raised when a webhook response does not return 200 status."""


def get_webhook_payload():
    """Return a sample payload to the request."""
    return {
        "json": {
            "hook": {
                "target": (
                    "https://webhook.site/491081ac-424b-4c4a-91b4-8cdbb5383ff0"
                ),
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


def test_webhook():
    """Used to test the webhook."""
    url = sys.argv[1]
    payload = get_webhook_payload()
    image_url = (
        "https://platerecognizer.com/wp-content/uploads/2020/07/"
        "ALPR-license-plate-reader-images-API.jpg"
    )
    image_response = requests.get(image_url)
    image = Image.open(BytesIO(image_response.content))
    files = {"upload": {"name": image}}
    try:
        response = requests.post(url, payload, files=files, timeout=30)
    except requests.exceptions.Timeout:
        raise WebhookError("The request timed out.")
    except requests.exceptions.TooManyRedirects:
        raise WebhookError(
            "The given URL might be misconfigured. "
            "Try a different one."
        )
    except requests.exceptions.RequestException as request_exception:
        raise WebhookError(str(request_exception)) from request_exception

    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.content}")

    if response.status_code >= 300:
        raise WebhookError(response.content)


if __name__ == "__main__":
    test_webhook()
