import json
import os
import urllib.parse
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError

upload_to = "uploads"


class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Send a POST request instead.")
        return

    def parse_multipart(self):
        """Return {field name: (filename, bytes)} for a multipart/form-data body.
        Replaces cgi.FieldStorage (the cgi module was removed in Python 3.13)."""
        body = self.rfile.read(int(self.headers["Content-Length"]))
        head = f"Content-Type: {self.headers['Content-Type']}\r\n\r\n".encode()
        msg = BytesParser(policy=HTTP).parsebytes(head + body)
        return {
            part.get_param("name", header="content-disposition"): (
                part.get_filename(),
                part.get_payload(decode=True),
            )
            for part in msg.iter_parts()
        }

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        if self.headers.get_content_type() == "multipart/form-data":
            form = self.parse_multipart()
            # Get webhook content
            json_data = form["json"][1].decode("utf-8") if "json" in form else None
            # Get webhook file
            if "upload" in form:
                filename, buffer = form["upload"]
                if not os.path.exists(upload_to):
                    try:
                        os.makedirs(upload_to)
                    except OSError:
                        print("Error creating directory:", upload_to)

                with open(f"./{upload_to}/{filename}", "wb") as fp:
                    print(f"Saving image to {filename}")
                    fp.write(buffer)

        else:
            raw_data = self.rfile.read(int(self.headers["content-length"])).decode(
                "utf-8"
            )
            if raw_data.startswith("json="):
                raw_data = raw_data[5:]
            try:
                decoded_data = urllib.parse.unquote(raw_data)
                decoded_data = decoded_data.replace("+", " ")
                json_data = json.loads(decoded_data)
            except JSONDecodeError:
                json_data = {}
        print(json_data)
        self.wfile.write(b"OK")


if __name__ == "__main__":
    server = HTTPServer(("", 8001), GetHandler)
    print("Starting server, use <Ctrl-C> to stop")
    server.serve_forever()
