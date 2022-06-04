import logging
import os
import sys
import cgi
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError
import requests
from requests.auth import HTTPDigestAuth

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style='{',
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)

USERNAME = os.getenv('USERNAME', None)
PASSWORD = os.getenv('PASSWORD', None)
VMS_API = os.getenv('VMS_API', None)
CAMERA_UID = os.getenv('CAMERA_UID', None)

if USERNAME is None or PASSWORD is None or VMS_API is None or CAMERA_UID is None:
    raise Exception('USERNAME, PASSWORD or VMS_API Not Set.')


def notify_nx(source, description, timestamp):
    lgr.debug(f'Notify NX Source: {source}, Description: {description}, timestamp: {timestamp}')
    endpoint = '/api/createEvent'
    metadata = json.dumps({
        'cameraRefs': [
            CAMERA_UID
        ]
    }, separators=(',', ':'))

    res = requests.get(
        VMS_API + endpoint,
        params={
            'timestamp': timestamp,
            'source': source,
            'caption': 'New Plate Detection',
            'metadata': metadata,
            'description': description,
            'state': 'InActive'
        },
        auth=HTTPDigestAuth(USERNAME, PASSWORD),
        verify=False
    )

    lgr.debug(f'NX Res: {res}')


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Send a POST request instead.')
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        if ctype == 'multipart/form-data':
            pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
            fields = cgi.parse_multipart(self.rfile, pdict)
            # Get webhook content
            json_data = json.loads(fields.get('json')[0])

        else:
            raw_data = self.rfile.read(int(
                self.headers['content-length'])).decode('utf-8')
            if raw_data.startswith('json='):
                raw_data = raw_data[5:]
            try:
                json_data = json.loads(raw_data)
            except JSONDecodeError:
                json_data = {}

        lgr.info('json_data:')
        lgr.info(json_data)

        data = json_data['data']
        camera_id = data['camera_id']
        timestamp = data['timestamp']

        # Pick first place from results
        plate = None
        for result in data['results']:
            plate = result['plate']
            break

        if plate is not None:
            notify_nx(camera_id, plate, timestamp)

        self.wfile.write(b'OK')


if __name__ == '__main__':
    server = HTTPServer(('', 8001), RequestHandler)
    lgr.info('Starting Webhook Receiver Server, use <Ctrl-C> to stop')
    server.serve_forever()
