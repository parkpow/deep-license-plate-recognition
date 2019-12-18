#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import os
import cv2

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from a RTSP stream and save the result in a CSV file.',
        epilog=
        'For example: anpr_camera_stream.py --camera rtsp://192.168.1.2:8080/out.h264 --api-key TOKEN --regions fr --output /path/to/output_dir/'
    )
    parser.add_argument('--api-key', help='Your API key.', required=True)
    parser.add_argument('--camera', help='RTSP stream url.', required=True)
    parser.add_argument('--regions', help='Regions e.g fr.', required=False)
    parser.add_argument('--output', help='output dir for the csv file and the encoded images ', required=True)
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    csv_output = os.path.join(args.output, 'output.csv')
    images_output = os.path.join(args.output, 'images')

    cap = cv2.VideoCapture(args.camera)

    while(1):
        ret, frame = cap.read()
        cv2.imshow('VIDEO', frame)
        cv2.waitKey(5)

if __name__ == "__main__":
    main()