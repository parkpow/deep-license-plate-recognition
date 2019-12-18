#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import cv2

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from a RTSP camera stream and out the result to a csv file.',
        epilog=
        'For example: python anpr_camera_stream.py --camera rtsp://192.168.1.2:8080/out.h264 --api-key TOKEN --regions fr --output /path/to/save.csv'
    )
    parser.add_argument('--camera', help='Url to a RTSP stream, ', required=True)
    parser.add_argument('--api-key', help='Your API key.', required=True)
    parser.add_argument('--regions', help='Region', required=False )
    parser.add_argument('--output-dir',
                        help='CSV output path, ',
                        required=False)
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    camera = cv2

if __name__ == "__main__":
    main()    

