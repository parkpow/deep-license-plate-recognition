import base64
import logging
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

from flask import Flask, request

from parkpow import ParkPowApi

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


def parse_event_xml(xml_data):
    # TODO include <vehicleType> <vehicleInfo>, <DeviceGPSInfo>, <countryAbbreviation>
    namespaces = {"ns": "http://www.hikvision.com/ver20/XMLSchema"}
    try:
        root = ET.fromstring(xml_data)
        event_type = root.find(".//ns:eventType", namespaces).text
        lgr.debug(f"Event Type: {event_type}")
        assert event_type == "ANPR"

        date_time = root.find(".//ns:dateTime", namespaces).text
        camera_id = root.find(".//ns:ipAddress", namespaces).text

        anpr = root.find(".//ns:ANPR", namespaces)
        license_place = anpr.find("ns:licensePlate", namespaces).text
        confidence = anpr.find("ns:confidenceLevel", namespaces).text

        picture_info_list = anpr.find("ns:pictureInfoList", namespaces)

        plate_coordinates = None
        for picture_info in picture_info_list:
            plate_rect = picture_info.find("ns:plateRect", namespaces)

            if plate_rect is not None:
                x = plate_rect.find("ns:X", namespaces).text
                y = plate_rect.find("ns:Y", namespaces).text
                width = plate_rect.find("ns:width", namespaces).text
                height = plate_rect.find("ns:height", namespaces).text
                plate_coordinates = [int(x), int(y), int(width), int(height)]
                break

        return license_place, confidence, plate_coordinates, date_time, camera_id
    except ET.ParseError as e:
        lgr.error(f"Error parsing XML: {e}")
        raise


def upload_event(xml_data, image):
    (license_plate_number, confidence, plate_coordinates, date_time, camera_id) = (
        parse_event_xml(xml_data)
    )

    parkpow.log_vehicle(
        image,
        license_plate_number,
        int(confidence) / 100,
        camera_id,
        datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S%z"),
        plate_coordinates,
    )


@app.route("/", methods=["POST"])
def process_files():
    """
    Process uploaded event and image files
    """

    # Check if event file exists
    if "anpr.xml" not in request.files:
        return "Event file missing", 400

    # Check if image file exists
    if "licensePlatePicture.jpg" not in request.files:
        return "Image file missing", 400

    event_file = request.files["anpr.xml"]
    # Read the file content
    xml_data = event_file.read()

    image_file = request.files["licensePlatePicture.jpg"]
    file_content = image_file.read()
    image = base64.b64encode(file_content).decode("utf-8")

    try:
        upload_event(xml_data, image)
        return "Files uploaded successfully", 200
    except Exception as e:
        return f"Error uploading files: {e}", 400
