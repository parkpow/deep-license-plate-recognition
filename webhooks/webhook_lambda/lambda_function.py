import base64
import json
from urllib.parse import unquote_plus


def print_vehicle_info(results):
    for result in results:
        print("Vehicle detected:")
        print("Plate: ", result["candidates"][0]["plate"])
        print("Color: ", result["color"][0]["color"])
        print(
            "Make - Model: ",
            result["model_make"][0]["make"] + " - " + result["model_make"][0]["model"],
        )
        print("Orientation: ", result["orientation"][0]["orientation"])


def handle_payload_with_image(body, boundary):
    # Split the body into parts using the boundary
    parts = body.split(b"--" + boundary.encode("utf-8"))

    # Filter out empty parts
    parts = [part for part in parts if part.strip()]

    # Process each part
    for part in parts:
        try:
            # Separate headers and content
            headers, content = part.split(b"\r\n\r\n", 1)
        except ValueError:
            # Skip if the part is not valid
            continue

        # Handle JSON data
        if b"json" in headers:
            data = json.loads(content.decode("utf-8"))
            results = data["data"]["results"]
            print_vehicle_info(results)

        # Handle image
        if b"upload" in headers:
            # Add logic to handle image
            pass


def handle_payload(body):
    # Handle JSON data
    if b"json" in body:
        content = unquote_plus(body.split(b"json=")[1].decode("utf-8"))
        data = json.loads(content)
        results = data["data"]["results"]
        print_vehicle_info(results)


def lambda_handler(event, context):
    # Retrieve the raw request body from the Lambda event
    body = base64.b64decode(event["body"])

    # Extract content type and boundary from headers
    content_type = event["headers"]["content-type"]

    split_by_boundary = content_type.split("boundary=")

    if len(split_by_boundary) > 1:
        # There is image included in payload
        boundary = split_by_boundary[1]
        handle_payload_with_image(body, boundary)

    else:
        handle_payload(body)

    # Return a response
    response = {"statusCode": 200, "body": "Webhook processing successful"}
    return response
