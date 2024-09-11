import json
import os
from io import BytesIO
from typing import Any

import requests
from PIL import Image


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
        return "No file uploaded.", 400

    plate_bounding_box = json_data["data"]["results"][0]["box"]
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
        return "Webhook request sent successfully.", response.status_code
    else:
        return "Webhook request failed.", response.status_code
