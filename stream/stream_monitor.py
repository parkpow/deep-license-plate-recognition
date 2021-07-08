import os
import time
import logging
import sys
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
from functools import partial
from datetime import datetime, timedelta
import argparse
import re

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

_state = {'container_active': False, 'last_log_times': {}}

log_line_regex = r'(\w+):([^:]*):(.*):\b'
compiled = re.compile(log_line_regex)


class GetHandler(BaseHTTPRequestHandler):

    def __init__(self, offline_diff_duration, *args, **kwargs):
        self.offline_diff_duration = offline_diff_duration
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        logging.debug('state: ')
        logging.debug(_state)

        online_time = datetime.now() - timedelta(
            seconds=self.offline_diff_duration)
        response = {'active': _state['container_running']}

        cameras = {}

        for k, v in _state['last_log_times'].items():
            logging.debug(f'Comparing times: [{v}] and [{online_time}]')
            if online_time < v:
                cameras[k] = {"status": "running"}
            else:
                cameras[k] = {"status": "offline"}

        response['cameras'] = cameras

        logging.debug('response')
        logging.debug(response)
        self.wfile.write(json.dumps(response).encode())
        self.wfile.write(b'\n')


def parse_log_line(line):
    """
    :param line: Stream log line
    :return: Log split into [level, camera, time]
    """
    m = compiled.match(line)
    if m:
        groups = m.groups()
        return [groups[0], groups[1], groups[2]]


def monitor_worker(container_name, check_interval):
    captures = 0
    previous_log_time = None

    while True:
        result = subprocess.run(
            ['docker', 'logs', '--tail', '1', container_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        docker_log = result.stdout.decode('utf-8')
        logging.debug(f'docker_log: {docker_log}')

        if 'No such container' in docker_log:
            _state['container_running'] = False
            time.sleep(check_interval)
            continue
        else:
            _state['container_running'] = True

        if len(docker_log) > 0:
            log_line = parse_log_line(docker_log)
            logging.debug(f'log_line: {log_line}')
            if log_line:
                log_time = log_line[2]
                if previous_log_time and log_time == previous_log_time:
                    logging.debug('No new logs detected')
                else:
                    camera = log_line[1]
                    _state['last_log_times'][camera] = datetime.now()
                    captures += 1
                    previous_log_time = log_time
        else:
            logging.debug('Log line empty')

        time.sleep(check_interval)
        logging.debug(f'Captures: {captures}')


def server_worker(host, port, offline_diff_duration):
    handler = partial(GetHandler, offline_diff_duration)
    server = HTTPServer((host, port), handler)
    logging.info('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Container Name
    parser.add_argument("-c",
                        "--container",
                        type=str,
                        default='stream',
                        help="Stream Container Name or ID")
    # Server listening HOST and PORT
    parser.add_argument("-l",
                        "--listen",
                        type=str,
                        default='localhost',
                        help="Server listen address")
    parser.add_argument("-p",
                        "--port",
                        type=int,
                        default=8001,
                        help="Server listen port")
    # Check Interval
    parser.add_argument("-i",
                        "--interval",
                        type=int,
                        default=2,
                        help="Interval between reading logs in seconds")
    # Active Duration
    parser.add_argument(
        "-d",
        "--duration",
        type=int,
        default=20,
        help="Duration to use in considering a camera as offline in seconds")

    args = parser.parse_args()
    monitor = threading.Thread(target=monitor_worker,
                               args=(args.container, args.interval))
    server = threading.Thread(target=server_worker,
                              args=(args.listen, args.port, args.duration))
    monitor.start()
    server.start()
