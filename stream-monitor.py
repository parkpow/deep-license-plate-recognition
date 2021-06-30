import os
import time
import logging
import sys
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
from datetime import datetime, timedelta

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# Duration to consider a camera to be offline if not generating new logs
OFFLINE_DIFF_DURATION = 20  # In Seconds
# Interval between reading logs
CHECK_INTERVAL = 2  # In Seconds

STATE = {'container_active': False, 'last_log_times': {}}


class GetHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        logging.debug('state: ')
        logging.debug(STATE)

        online_time = datetime.now() - timedelta(seconds=OFFLINE_DIFF_DURATION)
        response = {'active': STATE['container_running']}

        cameras = {}

        for k, v in STATE['last_log_times'].items():
            logging.debug(f'Comparing times: [{v}] and [{online_time}]')
            if online_time < v:
                cameras[k] = {"status": "running"}
            else:
                cameras[k] = {"status": "offline"}

        response['cameras'] = cameras

        logging.debug('response')
        logging.debug(response)
        self.wfile.write(json.dumps(response))
        self.wfile.write(b'\n')


def parse_log_line(line):
    """
    :param line: Stream log line
    :return: Log split into [level, camera, time, rest]
    """

    line_split = line.split(':', 2)
    print(line_split)

    log_level = line_split[0]
    camera = line_split[1]
    time_rest = line_split[2]
    time, rest = time_rest.split(' ', 1)

    return [log_level, camera, time.rstrip(':'), rest.rstrip('\r\n')]


def monitor_worker():
    captures = 0
    # now = 0
    previous_log_time = None

    while True:
        result = subprocess.run(['docker', 'logs', '--tail', '1', 'stream'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

        docker_log = result.stdout.decode('utf-8')
        logging.debug(docker_log)

        if 'No such container' in docker_log:
            STATE['container_running'] = False
            time.sleep(CHECK_INTERVAL)
            continue
        else:
            STATE['container_running'] = True

        if len(docker_log) > 0:
            log_line = parse_log_line(docker_log)

            logging.debug(log_line)
            log_time = log_line[2]

            if previous_log_time and log_time == previous_log_time:
                logging.debug('No new logs detected')
            else:
                if 'Health Score' in log_line[3] or 'New vehicle' in log_line[
                        3] or 'Model Optimization' in log_line[3]:
                    camera = log_line[1]
                    STATE['last_log_times'][camera] = datetime.now()

                captures += 1
                previous_log_time = log_time
        else:
            logging.debug('Log line empty')

        time.sleep(CHECK_INTERVAL)
        logging.debug(f'Captures: {captures}')


def server_worker():
    server = HTTPServer(('', 8001), GetHandler)
    print('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()


if __name__ == '__main__':
    server = threading.Thread(target=server_worker)
    monitor = threading.Thread(target=monitor_worker)
    monitor.start()
    server.start()
