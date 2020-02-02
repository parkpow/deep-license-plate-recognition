#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import csv
import io
import os
from datetime import datetime
from threading import Thread

import cv2
import requests
from PIL import Image

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from a RTSP stream and save the result in a CSV file.',
        epilog=
        'For example: anpr_camera_stream.py --camera rtsp://192.168.1.2:5554/camera --api-key TOKEN --regions fr --output /path/to/output.csv'
    )
    parser.add_argument('--api-key', help='Your API key.', required=True)
    parser.add_argument('--camera', help='RTSP stream url.', required=True)
    parser.add_argument(
        '--regions',
        help='Regions http://docs.platerecognizer.com/#regions-supported.',
        required=False)
    parser.add_argument('--output', help='CSV output file.', required=True)
    parser.add_argument(
        '--show-image',
        help='Show a window with the frame being sent for recognition.',
        action='store_true')
    parser.add_argument(
        '--inference-server',
        help='Server used for recognition. Default to cloud server.',
        default='https://api.platerecognizer.com/v1/plate-reader/')
    return parser.parse_args()


class ThreadedCamera(object):

    def __init__(self, args):
        self.capture = cv2.VideoCapture(args.camera, cv2.CAP_FFMPEG)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not self.capture.isOpened():
            print('No stream available: ' + args.camera)
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()
        self.frame = None
        self.status = False

    def update(self):
        while self.capture.isOpened():
            (self.status, self.frame) = self.capture.read()

    def get_frame(self,):
        if self.frame is None or not self.status:
            return
        cv2.waitKey(1)
        return self.frame


def capture(args, writer):
    camera = ThreadedCamera(args)
    while camera.capture.isOpened():
        frame = camera.get_frame()
        if frame is None:
            continue
        if args.show_image:
            cv2.imshow('frame', frame)

        buffer = io.BytesIO()
        im = Image.fromarray(frame)
        im.save(buffer, 'JPEG')
        buffer.seek(0)
        response = requests.post(
            args.inference_server,
            files=dict(upload=buffer),
            data=dict(regions=args.regions or ''),
            headers={'Authorization': 'Token ' + args.api_key})
        res = response.json()
        for result in res['results']:
            writer.writerow(
                dict(date=datetime.today().strftime('%x %X'),
                     license_plate=result['plate'],
                     score=result['score'],
                     dscore=result['dscore'],
                     vehicle_type=result['vehicle']['type']))


def main():
    args = parse_arguments()
    with open(args.output, 'w') as output:
        fields = ['date', 'license_plate', 'score', 'dscore', 'vehicle_type']
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        capture(args, writer)


if __name__ == "__main__":
    main()
