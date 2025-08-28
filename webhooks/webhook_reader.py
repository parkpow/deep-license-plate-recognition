import cgi
import json
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError

upload_to = "uploads"


class GetHandler(BaseHTTPRequestHandler):
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
        if ctype == "multipart/form-data":
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers["Content-Type"],
                },
            )
            # Get webhook content
            json_data = form.getvalue("json")
            # Get webhook file
            if "upload" in form:
                filename = form["upload"].filename
                buffer = form["upload"].file.read()
                if not os.path.exists(upload_to):
                    try:
                        os.makedirs(upload_to)
                    except OSError:
                        print("Error creating directory:", upload_to)

                with open(f"./{upload_to}/{filename}", "wb") as fp:
                    print("Saving image to %s" % filename)
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
