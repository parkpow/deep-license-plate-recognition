"""

Script designed to use multiple Parkpow's, from different data sources using a single Snapshot based on  Camera_Id.

instructions: 

python3 file_name.py

"""

import requests
from flask import Flask, request, jsonify
import json


app = Flask(__name__)


set_parkpow = {
    "camera1": {
        "url": "http://localhost:8000/api/v1/webhook-receiver/",
        "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    },
    "camera2": {
        "url": "http://localhost:8001/api/v1/webhook-receiver/",
        "token": "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
    },
    # Add more Parkpow´s and their information here
    # Camera1 and Camra2 represent the camera_id that is sent in the initial request
}

@app.route("/", methods=["GET", "POST"])
def handle_event():
    if request.method == "GET":
        return jsonify({"error": "Method not allowed"}), 405
    else:

        if 'upload' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['upload']
        filename = file.filename


        if not file:
            return jsonify({'error': 'Empty file uploaded'}), 400


        original_data = request.form['json']

        json_data = json.loads(original_data)

        camera_id = json_data["data"]["camera_id"]

        if not camera_id:
            return jsonify({'error': 'Camera_id not submitted'}), 400


        headers = {
            'Authorization': f'Token {set_parkpow[camera_id]["token"]}',
            'Content-Type': None
        }
      

        response = requests.post(set_parkpow[camera_id]["url"], headers=headers, files={"upload": (filename, file.read())}, data={"json": original_data})

        return response.content, response.status_code, response.headers.items()



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8181)
