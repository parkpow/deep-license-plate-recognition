import os
import sys
import cgi
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import logging
from urllib.parse import parse_qs
import configparser

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    format="{asctime} {levelname} {name} {threadName} : {message}")

lgr = logging.getLogger(__name__)


def read_config():
    """
    Read Config.ini File
    :return:
    """
    parser = configparser.ConfigParser()
    lgr.debug('Reading Configuration File')
    parser.read('config.ini')
    try:
        return parser['tag-update']
    except Exception:
        lgr.error('Invalid Configuration File')


def update_vehicle_tag(vehicle_id, tag, check, api_token):
    """
    Update ParkPow Vehicle TAGS

    :param vehicle_id:
    :param tag:
    :param check:
    :return:
    """
    lgr.debug(f'update_vehicle_tag({vehicle_id},{tag},{check})')
    base_url = os.getenv('BASE_URL', "https://app.parkpow.com")

    res = requests.post(f'{base_url}/api/v1/edit-tags/',
                        params={
                            'checked': 'true' if check else 'false',
                            'tag_id': tag,
                            'vehicle_id': vehicle_id
                        },
                        headers={'Authorization': 'Token ' + api_token})

    lgr.debug(f'Response: {res}')
    lgr.debug(f'Content: {res.text}')

    return res


def process_alert(config, raw_data, parkpow_api_token):
    """
    Select vehicle_tag from Alert, Check Config and Make Updates

    :param raw_data:
    :param config:
    :return:
    """
    data = parse_qs(raw_data)
    lgr.debug(json.dumps(data, indent=2))

    if 'vehicle_tag' in data:
        vehicle_tag = data['vehicle_tag']
        lgr.debug(f'vehicle_tag: {vehicle_tag}')

        if vehicle_tag in config:
            new_vehicle_tag = config[vehicle_tag]
            lgr.debug(f'new_vehicle_tag: {new_vehicle_tag}')

            vehicle_id = data['vehicle_id']
            lgr.debug(f'vehicle_id: {vehicle_id}')

            # Removing old Tag
            update_vehicle_tag(vehicle_id, vehicle_tag, False,
                               parkpow_api_token)

            # Adding new Tag
            update_vehicle_tag(vehicle_id, new_vehicle_tag, True,
                               parkpow_api_token)

        else:
            lgr.debug('Skipped missing vehicle tag')

    else:
        lgr.debug('Skipped alert with no vehicle tag')


class AlertRequestHandler(BaseHTTPRequestHandler):
    """
    Receive Alerts from ParkPow Webhook
    """

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Send a POST request instead.')
        return

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        content_type, options = cgi.parse_header(self.headers['Content-Type'])

        lgr.debug(f'Server config: {self.server.config}')
        if content_type == 'application/x-www-form-urlencoded':
            raw_data = self.rfile.read(int(
                self.headers['content-length'])).decode('utf-8')
            lgr.debug(f'raw_data: {raw_data}')

            process_alert(self.server.config, raw_data,
                          self.server.parkpow_api_token)

        else:
            lgr.error('Invalid content type')

        self.wfile.write(b'OK')


class TagsUpdaterServer(HTTPServer):

    def __init__(self,
                 server_address,
                 config,
                 parkpow_api_token,
                 handler_class=AlertRequestHandler):
        super().__init__(server_address, handler_class)
        self.config = config
        self.parkpow_api_token = parkpow_api_token


if __name__ == '__main__':
    config = read_config()
    parkpow_api_token = os.getenv('TOKEN', None)
    if parkpow_api_token is None:
        lgr.error('Missing required env variable TOKEN')
        exit(1)

    server = TagsUpdaterServer(('', 8001), config, parkpow_api_token,
                               AlertRequestHandler)
    lgr.info('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()
