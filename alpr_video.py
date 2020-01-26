#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import io
import json
import time

import requests
from PIL import Image

import cv2


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from a video and output the result as JSON.',
        epilog=
        'For example: python alpr_video.py --api MY_API_KEY --start 900 --end 2000 --skip 3 "/path/to/cars.mp4"'
    )
    parser.add_argument('--api', help='Your API key.', required=True)
    parser.add_argument('--start',
                        help='Start reading from this frame.',
                        type=int)
    parser.add_argument('--end', help='End reading after this frame.', type=int)
    parser.add_argument('--skip', help='Read 1 out of N frames.', type=int)
    parser.add_argument('FILE', help='Path to video.')
    return parser.parse_args()


def main():
    args = parse_arguments()
    result = []
    cap = cv2.VideoCapture(args.FILE)
    frame_id = 0
    while (cap.isOpened()):
        ret, frame = cap.read()
        frame_id += 1
        if args.skip and frame_id % args.skip != 0:
            continue
        if args.start and frame_id < args.start:
            continue
        if args.end and frame_id > args.end:
            break
        print('Reading frame %s' % frame_id)
        imgByteArr = io.BytesIO()
        im = Image.fromarray(frame)
        im.save(imgByteArr, 'JPEG')
        imgByteArr.seek(0)
        response = requests.post(
            'https://api.platerecognizer.com/v1/plate-reader/',
            files=dict(upload=imgByteArr),
            headers={'Authorization': 'Token ' + args.api})
        result.append(response.json())
        time.sleep(1)
    print(json.dumps(result, indent=2))
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
