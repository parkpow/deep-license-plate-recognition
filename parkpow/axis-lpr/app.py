import base64
import json
import logging
import os
import sys

from flask import Flask, request

from parkpow import ParkPowApi

# Based on https://www.axis.com/vapix-library/subjects/T10102231/section/t10165701/display?section=t10165701-t10165793

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)

app = Flask(__name__)

token = os.getenv("TOKEN")
pp_url = os.getenv("PP_URL")

parkpow = ParkPowApi(token, pp_url)


def upload_event(event, image):
    # TODO Take more fields into account during testing
    #  carID, imageType, carMoveDirection, plateCountry
    license_plate_number = event["plateUTF8"]
    confidence = event["plateConfidence"]
    camera_id = event["camera_info"]["SerialNumber"]
    capture_timestamp = event["capture_timestamp"]
    plate_coordinates = event["plateCoordinates"]

    parkpow.log_vehicle(
        image,
        license_plate_number,
        confidence,
        camera_id,
        capture_timestamp,
        plate_coordinates,
    )


@app.route("/", methods=["POST"])
def process_files():
    """Process uploaded event and image files"""

    # Check if event file exists
    if "event" not in request.files:
        return "Event file missing", 400

    # Check if image file exists
    if "image" not in request.files:
        return "Image file missing", 400

    event_file = request.files["event"]
    # Read the file content
    file_content = event_file.read()

    # Parse JSON data
    try:
        event = json.loads(file_content)
    except json.JSONDecodeError:
        return "Invalid JSON format", 400

    image_file = request.files["image"]
    file_content = image_file.read()
    image = base64.b64encode(file_content).decode("utf-8")

    try:
        upload_event(event, image)
        return "Files uploaded successfully", 200
    except Exception as e:
        return f"Error uploading files: {e}", 400
