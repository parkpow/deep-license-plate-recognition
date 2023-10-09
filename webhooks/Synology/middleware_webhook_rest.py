#!/usr/bin/python3.6
import cgi
import json
import base64
from urllib.parse import parse_qs
from urllib import parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import os

class GetHandler(BaseHTTPRequestHandler):
    def forward_to_rest_service(self, json_data):
        url = os.getenv('REST_SERVICE_URL')

        # The data from the plate regognizer
        timestamp = json_data['data']['timestamp_local']
        plate = json_data['data']['results'][0]['plate']

        # SVS support time, text1, text2, text3 to be the keys
        request_data = {
            'time': timestamp,
            'text1': plate,
        }

        # Headers for the request
        # SVS Support application/x-www-form-urlencoded
        HEADERS = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}

        # Encode the data
        data = parse.urlencode(request_data)

        # Send the request
        response = requests.post(url=url, headers=HEADERS, data=data)

        if response:
            print("rest request successful.")
            print("Response content: " + str(response))
        else:
            print("rest request failed.")

        return response

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Send a POST request instead.")
        return

    def do_POST(self):
        url = os.getenv('REST_SERVICE_URL')

        self.send_response(200)
        if not url:
            self.end_headers()
            self.wfile.write(b"REST_SERVICE_URL is not set.")
            return
        self.send_header("Content-type", "text/html")
        self.end_headers()
        ctype, pdict = cgi.parse_header(self.headers["Content-Type"])
        image_base64 = None
        if ctype == "multipart/form-data":
            pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
            fields = cgi.parse_multipart(self.rfile, pdict)
            # Get webhook content
            json_data = json.loads(fields.get("json")[0])
            try:
                buffer = fields.get("upload")[0]
                image_base64 = base64.b64encode(buffer).decode('utf-8')
            except:
                print("not file")
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

        self.forward_to_rest_service(json_data, image_base64)
        self.wfile.write(b"OK")

if __name__ == "__main__":
    server = HTTPServer(("", 8002), GetHandler)
    print("Starting server, use <Ctrl-C> to stop")
    server.serve_forever()
