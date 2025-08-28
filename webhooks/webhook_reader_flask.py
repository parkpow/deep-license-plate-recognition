"""
# Install flask
pip install Flask==1.1.2

# Run app
python3 webhook_reader_flask.py

"""

import errno
import json
import os

from flask import Flask, request

app = Flask(__name__)

upload_to = "uploads"


@app.route("/", methods=["GET", "POST"])
def process_request():
    if request.method == "GET":
        return "Send a POST request instead."
    else:
        # Files exist for multipart/form-data
        files = request.files
        if files:
            app.logger.debug(f"files: {files}")
            app.logger.debug("Request contains image")
            if not os.path.exists(upload_to):
                try:
                    os.makedirs(upload_to)
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            for key in files.keys():  # The file doesn't exist under upload
                app.logger.debug(f"key: {key}")
                f = files[key]
                f.save(f"{upload_to}/{f.filename}")
                break

            form = request.form
            json_data = json.loads(form["json"])
        else:
            app.logger.debug("Request contains json")
            form = request.form
            json_data = json.loads(form["json"])

        app.logger.debug(f"json_data: {json_data}")
        return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
