import cgi
import importlib
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Send a POST request instead.")

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        # Determine which middleware to use
        middleware_name = os.getenv("MIDDLEWARE_NAME")
        if not middleware_name:
            self.wfile.write(b"MIDDLEWARE_NAME environment variable is not set.")
            return

        try:
            middleware = importlib.import_module(f"middlewares.{middleware_name}")
        except ModuleNotFoundError:
            self.wfile.write(f"Middleware '{middleware_name}' not found.".encode())
            return

        ctype, pdict = cgi.parse_header(self.headers["Content-Type"])
        if ctype == "multipart/form-data":
            pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
            fields = cgi.parse_multipart(self.rfile, pdict)
            json_data = json.loads(fields.get("json")[0])
            upload_file = fields.get("upload")[0] if fields.get("upload") else None
        else:
            raw_data = self.rfile.read(int(self.headers["content-length"])).decode(
                "utf-8"
            )
            parsed_data = parse_qs(raw_data)
            dumps_data = json.dumps(parsed_data)
            parsed_data = json.loads(dumps_data)
            json_string = parsed_data["json"][0]
            json_data = json.loads(json_string)
            upload_file = None

        response = middleware.process_request(json_data, upload_file)

        self.wfile.write(response.encode())


def run_server():
    try:
        server = HTTPServer(("", 8002), WebhookHandler)
        logging.info("Started server on port 8002, use <Ctrl-C> to stop")
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user, shutting down...")
        sys.exit(0)
