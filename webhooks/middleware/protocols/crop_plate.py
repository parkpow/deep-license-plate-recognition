import json
import logging
import os
from io import BytesIO
from typing import Any

import requests
from PIL import Image

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def crop_image(image_data, crop_box):
    image = Image.open(BytesIO(image_data))
    cropped_image = image.crop(crop_box)
    cropped_image_buffer = BytesIO()
    cropped_image.save(cropped_image_buffer, format="JPEG")
    return cropped_image_buffer.getvalue()


def process_request(
    json_data: dict[str, Any], upload_file: bytes | None = None
) -> tuple[str, int]:
    if not upload_file:
        logging.error("No file uploaded.")
        return "No file uploaded.", 400

    data = json_data["data"]["results"][0]

    plate_bounding_box = data.get("box") or data["vehicle"]["box"]
    crop_box = (
        plate_bounding_box["xmin"],
        plate_bounding_box["ymin"],
        plate_bounding_box["xmax"],
        plate_bounding_box["ymax"],
    )
    cropped_image = crop_image(upload_file, crop_box)

    files = {
        "original_image": BytesIO(upload_file),
        "cropped_image": BytesIO(cropped_image),
    }
    data = {"json": json.dumps(json_data)}

    response = requests.post(os.getenv("WEBHOOK_URL", ""), data=data, files=files)

    if response.status_code == 200:
        logging.info("Webhook request sent successfully.")
        return "Webhook request sent successfully.", response.status_code
    else:
        logging.error(f"Webhook request failed. Response code: {response.status_code}")
        return "Webhook request failed.", response.status_code
