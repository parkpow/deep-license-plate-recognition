import logging
import os
import sys
import cgi
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from json.decoder import JSONDecodeError
import requests
from requests.auth import HTTPDigestAuth
import argparse
from functools import partial


LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style='{',
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)


def notify_nx(username, password, vms_api, camera_uid, source, description, timestamp):
    lgr.debug(f'Notify NX Source: {source}, Description: {description}, timestamp: {timestamp}')
    endpoint = '/api/createEvent'
    metadata = json.dumps({
        'cameraRefs': [
            camera_uid
        ]
    }, separators=(',', ':'))

    try:
        res = requests.get(
            vms_api + endpoint,
            params={
                'timestamp': timestamp,
                'source': source,
                'caption': 'New Plate Detection',
                'metadata': metadata,
                'description': description,
                'state': 'InActive'
            },
            auth=HTTPDigestAuth(username, password),
            verify=False
        )
        res.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        lgr.error("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        lgr.error("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        lgr.error("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        lgr.error("OOps: Something Else", err)


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, username, password, vms, camera, *args, **kwargs):
        self.username = username
        self.password = password
        self.vms = vms
        self.camera = camera
        super().__init__(*args, **kwargs)

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

        lgr.debug('json_data:')
        lgr.debug(json_data)

        data = json_data['data']
        camera_id = data['camera_id']
        timestamp = data['timestamp']

        # Pick first place from results
        plate = None
        for result in data['results']:
            plate = result['plate']
            break

        if plate is not None:
            notify_nx(self.username, self.password, self.vms, self.camera, camera_id, plate, timestamp)

        self.wfile.write(b'OK')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Forward Stream Webhook Events to NX VMS as Alerts.')
    parser.add_argument('--username', help='NX VMS Username.', required=True)
    parser.add_argument('--password', help='NX VMS Password.', required=True)
    parser.add_argument('--vms', help='VMS API Endpoint.', required=True)
    parser.add_argument('--camera', help='UID of Camera used as Source of Alerts.', required=True)

    args = parser.parse_args()

    handler = partial(RequestHandler, args.username, args.password, args.vms, args.camera)
    server = HTTPServer(('', 8001), handler)
    lgr.info('Starting Webhook Receiver Server, use <Ctrl-C> to stop')
    server.serve_forever()
