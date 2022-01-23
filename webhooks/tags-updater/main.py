import os
import sys
import cgi
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import logging
from urllib.parse import parse_qs
import configparser
import csv

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style='{',
    format="{asctime} {levelname} {name} {threadName} : {message}")

lgr = logging.getLogger(__name__)

USER_DATA_DIR = '/user-data/'
NO_TAGS = 'NO_TAGS'


def read_config():
    """
    Read Config.ini File
    :return:
    """
    parser = configparser.ConfigParser()
    lgr.debug('Reading Configuration File')
    try:
        parser.read(f'{USER_DATA_DIR}config.ini')
        settings = parser['settings']
        tag_update = parser['tag-update']
        return settings, tag_update
    except Exception:
        lgr.exception('Invalid Configuration File')


def list_vehicle_tags(api_token, base_url):
    """
    Download all vehicle tags into a map of name -> id
    :param api_token:
    :param base_url:
    :return:
    """
    vehicle_tags = {}

    page = 1
    while page > 0:
        lgr.debug(f'list_vehicle_tags page: {page}')
        res = requests.get(f'{base_url}/api/v1/vehicle-tags/',
                           params={'page': page},
                           headers={'Authorization': 'Token ' + api_token})

        if res.status_code == 200:
            tags = res.json()
            for tag in tags['results']:
                vehicle_tags[tag['name']] = tag['id']

            if tags['next']:
                page += 1
            else:
                page = 0
        else:
            raise Exception(
                f'An Error occurred listing vehicle tags: {res} {res.text}')

    lgr.debug(f'vehicle_tags: {vehicle_tags}')
    return vehicle_tags


def update_vehicle_tag(vehicle_id, tag_id, check, api_token, base_url):
    """
    Update ParkPow Vehicle TAGS

    :param vehicle_id:
    :param tag:
    :param check:
    :param api_token:
    :param base_url:
    :return:
    """
    lgr.debug(f'update_vehicle_tag({vehicle_id},{tag_id},{check})')

    res = requests.post(f'{base_url}/api/v1/edit-tags/',
                        params={
                            'checked': 'true' if check else 'false',
                            'tag_id': tag_id,
                            'vehicle_id': vehicle_id
                        },
                        headers={'Authorization': 'Token ' + api_token})

    lgr.debug(f'Response: {res}')
    lgr.debug(f'Content: {res.text}')

    if res.status_code != 200:
        lgr.error(
            f'An error occurred updating vehicle_id: {vehicle_id} tag:{tag_id} check:{check}'
        )
        return False

    return True


def process_vehicle_tag(vehicle_tag, data, vehicle_tags, parkpow_api_token,
                        parkpow_base_url):
    new_vehicle_tag = config[vehicle_tag]
    lgr.debug(f'new_vehicle_tag: {new_vehicle_tag}')

    vehicle_id = data['vehicle_id'][0]
    lgr.debug(f'vehicle_id: {vehicle_id}')

    # Removing old Tag
    if vehicle_tag == NO_TAGS:
        removal = True
    else:
        vehicle_tag_id = vehicle_tags[vehicle_tag]
        removal = update_vehicle_tag(vehicle_id, vehicle_tag_id, False,
                                     parkpow_api_token, parkpow_base_url)

    # Adding new Tag
    new_vehicle_tag_id = vehicle_tags[new_vehicle_tag]
    addition = update_vehicle_tag(vehicle_id, new_vehicle_tag_id, True,
                                  parkpow_api_token, parkpow_base_url)

    if addition and removal:
        return [
            data['license_plate'][0],
            data['time'][0], vehicle_tag, new_vehicle_tag
        ]


def process_alert(config_tags, raw_data, parkpow_api_token, parkpow_base_url,
                  parkpow_tags):
    """
    Select vehicle_tag from Alert, Check Config and Make Updates

    :param config:
    :param raw_data:
    :param parkpow_api_token:
    :param parkpow_base_url:
    :param vehicle_tags:
    :return:
    """
    data = parse_qs(raw_data)
    lgr.debug(json.dumps(data, indent=2))

    if 'vehicle_tag' in data:
        for vehicle_tag in data['vehicle_tag'][0].split(','):
            lgr.debug(f'processing vehicle_tag: {vehicle_tag}')
            if vehicle_tag in config_tags:
                return process_vehicle_tag(vehicle_tag, data, parkpow_tags,
                                           parkpow_api_token, parkpow_base_url)
            else:
                lgr.debug('Skipped missing vehicle tag')

    else:
        if NO_TAGS in config_tags:
            return process_vehicle_tag(NO_TAGS, data, parkpow_tags,
                                       parkpow_api_token, parkpow_base_url)
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

            log_file_path = f'{USER_DATA_DIR}update-log.csv'
            log_file_exists = os.path.exists(log_file_path)
            with open(log_file_path, 'a', newline='') as csv_file:
                log_writer = csv.writer(csv_file)
                if not log_file_exists:
                    log_writer.writerow(
                        ['Plate', 'Timestamp', 'Old Tag', 'New Tag'])
                    csv_file.flush()

                update = process_alert(self.server.config, raw_data,
                                       self.server.parkpow_api_token,
                                       self.server.parkpow_base_url,
                                       self.server.vehicle_tags)
                if update:
                    log_writer.writerow(update)
                    csv_file.flush()

        else:
            lgr.error('Invalid content type')

        self.wfile.write(b'OK')


class TagsUpdaterServer(HTTPServer):

    def __init__(self,
                 server_address,
                 config,
                 settings,
                 handler_class=AlertRequestHandler):
        super().__init__(server_address, handler_class)
        self.config = config
        self.parkpow_api_token = settings['parkpow_api_token']
        self.parkpow_base_url = settings.get('parkpow_base_url',
                                             'https://app.parkpow.com')
        self.vehicle_tags = list_vehicle_tags(self.parkpow_api_token,
                                              self.parkpow_base_url)


if __name__ == '__main__':
    settings, config = read_config()
    if not settings['parkpow_api_token']:
        lgr.error('Missing required parkpow_api_token')
        exit(1)

    server = TagsUpdaterServer(('', 8001), config, settings,
                               AlertRequestHandler)
    lgr.info('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()
