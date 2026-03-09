import json
import logging
import os
from io import BytesIO
from typing import Any

import requests
from PIL import Image, ImageDraw

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def annotate_image(image_data: bytes, bounding_box: dict[str, int]) -> bytes:
    """Draw a red rectangle around the plate bounding box on the image."""
    image = Image.open(BytesIO(image_data))
    draw = ImageDraw.Draw(image)
    coords = [
        bounding_box["xmin"],
        bounding_box["ymin"],
        bounding_box["xmax"],
        bounding_box["ymax"],
    ]
    draw.rectangle(coords, outline="red", width=3)
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def process_request(
    json_data: dict[str, Any], all_files: dict[str, bytes] | None = None
) -> tuple[str, int]:
    if not all_files:
        logging.error("No files uploaded.")
        return "No files uploaded.", 400

    upload_file = all_files.get("upload")

    if not upload_file:
        logging.error("No file uploaded.")
        return "No file uploaded.", 400

    data_results = json_data.get("data", {}).get("results")
    if not data_results:
        logging.error("No results found in data.")
        return "No results found in data.", 400

    data = data_results[0]
    plate_data = data.get("plate")

    if isinstance(plate_data, dict):
        plate = plate_data.get("props", {}).get("plate", [{}])[0].get("value")
        plate_bounding_box = plate_data.get("box")
    else:
        plate = plate_data
        plate_bounding_box = data.get("box")

    if not plate_bounding_box:
        logging.error("No bounding box found in the results.")
        return "No bounding box found.", 400

    try:
        annotated_image = annotate_image(upload_file, plate_bounding_box)
    except (KeyError, ValueError, OSError) as err:
        logging.error(f"Failed to annotate image: {err}")
        return "Failed to annotate image.", 400

    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        logging.error("WEBHOOK_URL environment variable is not set.")
        return "WEBHOOK_URL not configured.", 500

    files = {"upload": ("upload.jpg", BytesIO(annotated_image), "image/jpeg")}
    data_payload = {"json": json.dumps(json_data)}

    response = None
    try:
        response = requests.post(
            webhook_url, data=data_payload, files=files, timeout=10
        )
        response.raise_for_status()
        logging.info(f"Vehicle: {plate}. Request was successful.")
        return "Request was successful", response.status_code
    except requests.exceptions.RequestException as err:
        logging.error(f"Vehicle: {plate}. Error processing the request: {err}")
        status_code = response.status_code if response is not None else 503
        return f"Failed to process the request: {err}", status_code
