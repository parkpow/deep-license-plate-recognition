#!/usr/bin/python3.6
import cgi
import json
import argparse
import requests
from datetime import datetime
from urllib.parse import parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from PIL import Image

class GetHandler(BaseHTTPRequestHandler):

    def crop_image(self, image_data, crop_box):
        image = Image.open(BytesIO(image_data))
        cropped_image = image.crop(crop_box)
        cropped_image_buffer = BytesIO()
        cropped_image.save(cropped_image_buffer, format="JPEG")

        return cropped_image_buffer.getvalue()

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Send a POST request instead.")
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        ctype, pdict = cgi.parse_header(self.headers["Content-Type"])
        pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
        if ctype == "multipart/form-data":
            fields = cgi.parse_multipart(self.rfile, pdict)    
            #Get webhook json data content           
            json_data = json.loads(fields.get("json")[0])
            plate_bounding_box = json_data["data"]["results"][0]["box"]
            try:
                #Get webhook upload content (image)
                buffer = fields.get("upload")[0]
                #crop box (e.g., left, upper, right, lower)
                crop_box = (plate_bounding_box["xmin"], plate_bounding_box["ymin"], plate_bounding_box["xmax"], plate_bounding_box["ymax"])
                cropped_image = self.crop_image(buffer, crop_box)
                original_file = (fields.get("upload")[0])
                cropped_file = (BytesIO(cropped_image))
                files = {
                    'original_image': original_file,
                    'cropped_image': cropped_file
                }
                # Convert JSON data back to a string
                data = {
                "json": json.dumps(json_data)  
                }
                response = requests.post(cli_args.webhook_url, data=data, files=files)
              
                # Check the response from the webhook end point
                if response.status_code == 200:
                    self.wfile.write(b"Webhook request sent successfully.")
                else:
                    self.wfile.write(b"Webhook request failed.")
                  
            except:
                print("not a file")
        else:
            raw_data = self.rfile.read(int(self.headers["content-length"])).decode(
                "utf-8"
            )
            # Parse the form data into a dictionary
            parsed_data = parse_qs(raw_data)
            # Convert the dictionary to JSON format
            dumps_data = json.dumps(parsed_data)
            parsed_data = json.loads(dumps_data)
            # Extract the nested JSON string from the list
            json_string = parsed_data['json'][0]
            # Parse the nested JSON string
            json_data = json.loads(json_string)
            print(json_data)

        self.wfile.write(b"OK")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Receive webhook POST function and forward it to a SOAP service",
        epilog="",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.epilog += (
        "Examples:\n"
        "Crop license plate image from original or vehicle image incoming in Stream/Snapshot webhook, append and forward to another webhook endpoint: "
        "./webhook_crop_image_middleware.py --webhook-url https://your-webhook-site.com/endpoint"
    )

    parser.add_argument(
        "-s",
        "--webhook-url",
        help="webhook url to forward original data with cropped image included",
        required=False,
    )
  
    cli_args = parser.parse_args()

    if not cli_args.webhook_url:
        raise Exception("webhook-url is required")

    server = HTTPServer(("", 8002), GetHandler)
    print("Starting server, use <Ctrl-C> to stop")
    server.serve_forever()
