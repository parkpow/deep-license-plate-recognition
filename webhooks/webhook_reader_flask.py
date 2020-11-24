"""
# Install flask
pip install Flask==1.1.2

# Run app
export FLASK_APP=app.py
export FLASK_DEBUG=1
python3 -m flask run -h 0.0.0.0 -p 8001

"""

from flask import Flask
from flask import request
import json
import os
import errno

app = Flask(__name__)

upload_to = 'uploads'


@app.route('/', methods=['GET', 'POST'])
def process_request():
    if request.method == 'GET':
        return 'Send a POST request instead.'
    else:
        # Files exist for multipart/form-data
        files = request.files
        app.logger.debug(f'files: {files}')
        if files:
            app.logger.debug('Request contains image')
            if not os.path.exists(upload_to):
                try:
                    os.makedirs(upload_to)
                except OSError as exc:  # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise

            for key in files.keys():  # The file doesn't exist under upload
                app.logger.debug(f'key: {key}')
                f = files[key]
                f.save(f'{upload_to}/{f.filename}')
                break

            form = request.form
            json_data = json.loads(form['json'])
        else:
            app.logger.debug('Request contains json')
            json_data = request.json

        app.logger.debug(f'json_data: {json_data}')
        return 'OK'
