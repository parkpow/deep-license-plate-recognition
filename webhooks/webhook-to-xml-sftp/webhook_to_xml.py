import argparse
import base64
import cgi
import json
import logging
import os
import re
import sys
from configparser import ConfigParser
from datetime import datetime
from urllib.parse import parse_qs
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement

import paramiko
from flask import Flask, jsonify, request
from waitress import serve

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)

app = Flask(__name__)

config = ConfigParser()
config.read("config.ini")


def handle_user_data(user_data):
    consistent_string = re.sub(r"(?<=\w),(?=\w)", ", ", user_data)
    pairs = consistent_string.strip("{}").split(",")

    data_dict = {}

    # Process each key-value pair
    for pair in pairs:
        key, value = pair.split(":")
        key = key.strip("'").replace("{", "").strip(" ")
        value = str(value)
        value = value.strip("'").replace("}", "").strip(" ")
        data_dict[key] = value
    return data_dict


def get_timestamp_in_file_name_format(timestamp):
    timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f%z")
    return timestamp_obj.strftime("%Y_%m_%d_%H_%M_%S")


def get_timestamp_in_xml_event_time_format(timestamp):
    dt = datetime.strptime(timestamp, "%H:%M:%S.%f%z")
    formatted_time = dt.strftime("%H:%M:%S")
    timezone_offset = dt.strftime("%z")
    formatted_timezone_offset = f"{timezone_offset[:-2]}:{timezone_offset[-2:]}"
    return f"{formatted_time}{formatted_timezone_offset}"


def format_json_to_xml(json_data, image, args):
    user_data = json_data["data"]["results"][0]["user_data"]

    if user_data:
        expected_fields = [
            "LPRCameraName",
            "LatitudeDegreeValue",
            "LatitudeMinuteValue",
            "LatitudeSecondValue",
            "LongitudeDegreeValue",
            "LongitudeMinuteValue",
            "LongitudeSecondValue",
        ]
        for field in expected_fields:
            if field in user_data:
                pass
            else:
                logging.error(
                    field
                    + " in webhook user_data field is missing, please see: https://guides.platerecognizer.com/docs/stream/configuration/#sending-additional-information-gps"
                )
                return None

        user_data_dict = handle_user_data(user_data)

    else:
        logging.error(
            "Webhook user data is missing, please see: https://guides.platerecognizer.com/docs/stream/configuration/#sending-additional-information-gps"
        )
        return None

    try:
        camera_id = json_data["data"]["camera_id"]
        plate = json_data["data"]["results"][0]["plate"]

        timestamp = json_data["data"]["timestamp_local"]
        date_str, time_str = timestamp.split()

        # Create the root element
        license_plate_reads = Element("LicensePlateReads")
        license_plate_read = SubElement(license_plate_reads, "lpr:LicensePlateRead")

        # Create the LicensePlateRead element
        license_plate_read.set(
            "xsi:schemaLocation",
            "http://www.it.ojp.gov/jxdm/3.0.3/license-plate-reader lpr-extension-schema.xsd",
        )
        license_plate_read.set("xsi:noNamespaceSchemaLocation", "document-schema.xsd")
        license_plate_read.set(
            "xmlns:lpr", "http://www.it.ojp.gov/jxdm/3.0.3/license-plate-reader"
        )
        license_plate_read.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        license_plate_read.set("xmlns:j", "http://www.it.ojp.gov/jxdm/3.0.3")

        # Add child elements to LicensePlateRead
        event_date = SubElement(license_plate_read, "j:EventDate")

        # expected format YYYY-MM-dd"
        event_date.text = date_str

        event_time = SubElement(license_plate_read, "j:EventTime")

        # expected format "HH:MM:ss-0H:00"
        event_time.text = get_timestamp_in_xml_event_time_format(time_str)

        lpr_system_id = SubElement(license_plate_read, "lpr:LPRSystemID")
        lpr_system_id.text = args.lpr_sys_id

        SubElement(license_plate_read, "lpr:ActivityReason")

        # To define
        lpr_event_id = SubElement(license_plate_read, "lpr:LPREventID")
        lpr_event_id.text = (
            camera_id + "_" + get_timestamp_in_file_name_format(timestamp)
        )

        organization_oriid = SubElement(license_plate_read, "j:OrganizationORIID")
        ogrganizaion_id_se = SubElement(organization_oriid, "j:ID")
        ogrganizaion_id_se.text = args.ori_id

        lpr_vehicle = SubElement(license_plate_read, "lpr:LPRVehicle")
        vehicle_license_plate_id = SubElement(lpr_vehicle, "j:VehicleLicensePlateID")
        vehicle_license_plate_id_se = SubElement(vehicle_license_plate_id, "j:ID")
        vehicle_license_plate_id_se.text = plate

        id_issuing_authority_text = SubElement(
            vehicle_license_plate_id, "j:IDIssuingAuthorityText"
        )
        id_issuing_authority_text.text = args.id_issuing_authority

        lpr_geographic_coordinate = SubElement(
            license_plate_read, "lpr:LPRGeographicCoordinate"
        )
        geographic_coordinate_latitude = SubElement(
            lpr_geographic_coordinate, "j:GeographicCoordinateLatitude"
        )
        latitude_degree_value = SubElement(
            geographic_coordinate_latitude, "j:LatitudeDegreeValue"
        )
        latitude_degree_value.text = user_data_dict["LatitudeDegreeValue"]
        latitude_minute_value = SubElement(
            geographic_coordinate_latitude, "j:LatitudeMinuteValue"
        )
        latitude_minute_value.text = user_data_dict["LatitudeMinuteValue"]
        latitude_second_value = SubElement(
            geographic_coordinate_latitude, "j:LatitudeSecondValue"
        )
        latitude_second_value.text = user_data_dict["LatitudeSecondValue"]

        geographic_coordinate_longitude = SubElement(
            lpr_geographic_coordinate, "j:GeographicCoordinateLongitude"
        )
        longitude_degree_value = SubElement(
            geographic_coordinate_longitude, "j:LongitudeDegreeValue"
        )
        longitude_degree_value.text = user_data_dict["LongitudeDegreeValue"]
        longitude_minute_value = SubElement(
            geographic_coordinate_longitude, "j:LongitudeMinuteValue"
        )
        longitude_minute_value.text = user_data_dict["LongitudeMinuteValue"]
        longitude_second_value = SubElement(
            geographic_coordinate_longitude, "j:LongitudeSecondValue"
        )
        longitude_second_value.text = user_data_dict["LongitudeSecondValue"]

        document_control_metadata = SubElement(
            license_plate_read, "j:DocumentControlMetadata"
        )
        document_country_code = SubElement(
            document_control_metadata, "j:DocumentCountryCode.fips10-4"
        )
        document_country_code.text = args.document_country_code

        lpr_camera_id = SubElement(license_plate_read, "lpr:LPRCameraID")
        lpr_camera_id.text = camera_id

        lpr_camera_name = SubElement(license_plate_read, "lpr:LPRCameraName")
        lpr_camera_name.text = user_data_dict["LPRCameraName"]

        # Image in base64 format
        lpr_vehicle_plate_photo = SubElement(
            license_plate_read, "lpr:LPRVehiclePlatePhoto"
        )
        lpr_vehicle_plate_photo.text = image

        xml_data = ElementTree.tostring(
            license_plate_reads, encoding="utf-8", method="xml"
        )

    except Exception as e:
        print(str(e))
        return
    return {"xml": xml_data, "timestamp": timestamp}


def send_to_sftp(file_data, args):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            args.sftp_host, args.sftp_host_port, args.sftp_username, args.sftp_password
        )
        sftp = ssh.open_sftp()
        timestamp_file_name_format = get_timestamp_in_file_name_format(
            file_data["timestamp"]
        )
        with sftp.file(
            args.sftp_remote_path
            + "plate_detection_"
            + timestamp_file_name_format
            + ".xml",
            "w",
        ) as file:
            file.write(file_data["xml"])
        sftp.close()
        ssh.close()
    except Exception as e:
        print(str(e))
        return


@app.route("/webhook", methods=["POST"])
def event_handler():
    try:
        image_base64 = None
        ctype, pdict = cgi.parse_header(request.headers["Content-Type"])
        if ctype == "multipart/form-data":
            pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
            fields = cgi.parse_multipart(request.stream, pdict)
            json_data = json.loads(fields.get("json")[0])
            try:
                buffer = fields.get("upload")[0]
                image_base64 = base64.b64encode(buffer).decode("utf-8")
            except TypeError as e:
                print(
                    "Error caught: "
                    + e
                    + "\nNot a file, check event sender image configuration."
                )
        else:
            raw_data = request.data.decode("utf-8")
            parsed_data = parse_qs(raw_data)
            dumps_data = json.dumps(parsed_data)
            parsed_data = json.loads(dumps_data)
            json_string = parsed_data["json"][0]
            json_data = json.loads(json_string)

        response_data = {
            "status": "success",
            "message": json_data["data"]["camera_id"]
            + " - Event received successfully",
        }
        logging.info(response_data["message"])

        xml_data = format_json_to_xml(json_data, image_base64, args)

        if not xml_data:
            response_data = {
                "status": "error",
                "message": json_data["data"]["camera_id"]
                + " - xml file couldn't be generated",
            }
            return jsonify(response_data), 400

        send_to_sftp(xml_data, args)

        return jsonify(response_data), 200

    except Exception as e:
        return str(e), 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Webhook server to receive JSON on /note route."
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", "0.0.0.0"),
        help="The host IP address to bind the server to.",
    )
    parser.add_argument(
        "--host_port",
        type=int,
        default=int(os.getenv("HOST_PORT", 5000)),
        help="The port number to bind the server to. (Optional - Default = 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=int(os.getenv("DEBUG", 0)),
        help="Turn on Flask debug mode. (Optional)",
    )
    parser.add_argument(
        "--sftp-host",
        type=str,
        default=os.getenv("SFTP_HOST", None),
        help="SFTP server host",
    )
    parser.add_argument(
        "--sftp-host_port",
        type=str,
        default=os.getenv("SFTP_HOST_PORT", "22"),
        help="SFTP server host port, default=22",
    )
    parser.add_argument(
        "--sftp-username",
        type=str,
        default=os.getenv("SFTP_USERNAME", None),
        help="SFTP server username",
    )
    parser.add_argument(
        "--sftp-password",
        type=str,
        default=os.getenv("SFTP_PASSWORD", None),
        help="SFTP server password",
    )
    parser.add_argument(
        "--sftp-remote-path",
        type=str,
        default=os.getenv("SFTP_REMOTE_PATH", None),
        help="SFTP server remote path to store file",
    )

    # custom args
    parser.add_argument(
        "--lpr_sys_id",
        type=str,
        default=config.get("app", "lpr_sys_id", fallback=None),
        help="LPR System ID",
    )
    parser.add_argument(
        "--ori_id",
        type=str,
        default=config.get("app", "ori_id", fallback=None),
        help="Organization ORI ID",
    )
    parser.add_argument(
        "--id_issuing_authority",
        default=config.get("app", "id_issuing_authority", fallback=None),
        type=str,
        help="ID Issuing Authority Text",
    )
    parser.add_argument(
        "--document_country_code",
        default=config.get("app", "document_country_code", fallback=None),
        type=str,
        help="Document Country Code (FIPS10-4)",
    )

    args = parser.parse_args()

    args.host = os.getenv("HOST", args.host)
    args.host_port = os.getenv("HOST_PORT", args.host_port)

    if (
        not args.lpr_sys_id
        or not args.ori_id
        or not args.id_issuing_authority
        or not args.document_country_code
    ):
        logging.error(
            "--lpr-sys-id, --ori-id, --id-issuing-authority and --document-country-code are required parameters, make sure to define it in params.txt file"
        )
        sys.exit(1)

    if not args.sftp_host or not args.sftp_password or not args.sftp_remote_path:
        logging.error(
            "--sftp-host, --sftp-username, --sftp-password, --sftp-remote-path are required parameters"
        )
        sys.exit(1)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    serve(app, host=args.host, port=args.host_port)
