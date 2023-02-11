"""
# Install flask
pip install Flask

# Run app
python3 webhook_test.py

optional parameters:
--port
--debug

for external access
--host=0.0.0.0

example:

python3 webhook_test.py --port=8001 --debug=1 --host==0.0.0.0

"""


import argparse
import requests
from flask import Flask, request, jsonify
import json

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def handle_event():
    if request.method == "GET":
        return jsonify({"error": "Method not allowed"}), 405
    else:
        request_data = request.form['json']
        print(json.loads(request_data))
        response = requests.post(
            "https://webhook.site/2acd1200-b90f-4a90-b43b-c0d83d2677c5", data={"data": request_data})
        return {"data": request_data, "status_code": response.status_code}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", type=int, default=0)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=bool(args.debug))
