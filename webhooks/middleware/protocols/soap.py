import base64
import os
from datetime import datetime
from typing import Any

from zeep import Client, Transport


def forward_to_SOAP_service(json_data, image):
    # Retrieve environment variables for the SOAP service
    soap_service_url = os.getenv("SOAP_SERVICE_URL")
    soap_action = "http://tempuri.org/PostImage"
    service_user = os.getenv("SOAP_USER")
    service_key = os.getenv("SOAP_SERVICE_KEY")

    timestamp = json_data["data"]["timestamp_local"]
    plate = json_data["data"]["results"][0].get("plate")
    score = json_data["data"]["results"][0].get("score")
    if plate and type(plate) != str:
        plate = json_data["data"]["results"][0]["props"]["plate"][0]["value"]
        score = json_data["data"]["results"][0]["props"]["plate"][0]["score"]

    # Format timestamp and filename
    parsed_timestamp = datetime.strptime(timestamp[:26], "%Y-%m-%d %H:%M:%S.%f")
    formatted_timestamp = parsed_timestamp.strftime("%-m/%-d/%Y %H:%M:%S")

    request_data = {
        "user": service_user,
        "password": service_key,
        "date": formatted_timestamp,
        "plate": plate,
        "score": score,
        "image": image,
    }

    # Headers for the request
    transport = Transport()
    transport.session.headers["Content-Type"] = "text/xml; charset=utf-8"
    transport.session.headers["SOAPAction"] = soap_action

    client = Client(soap_service_url, transport=transport)

    response = client.service.PostImage(**request_data)

    if response:
        return "SOAP request successful.", 200
    else:
        return "SOAP request failed.", 400


def process_request(
    json_data: dict[str, Any], upload_file: bytes | None = None
) -> tuple[str, int]:
    image_base64 = None
    if upload_file:
        image_base64 = base64.b64encode(upload_file).decode("utf-8")

    response = forward_to_SOAP_service(json_data, image_base64)
    return response
