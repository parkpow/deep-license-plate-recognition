#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from glob import glob
import argparse
import requests
import json
import time


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Read license plates from images and output the result as JSON.',
        epilog='For example: python plate_recognition.py --api MY_API_KEY "/path/to/vehicle-*.jpg"')
    parser.add_argument('--api', help='Your API key.', required=True)
    parser.add_argument('FILE', help='Path to vehicle image or pattern.')
    return parser.parse_args()


def main():
    args = parse_arguments()
    result = []
    paths = glob(args.FILE)
    if len(paths) == 0:
        print('File {} does not exist.'.format(args.FILE))
        return
    for path in paths:
        with open(path, 'rb') as fp:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                files=dict(upload=fp),
                headers={'Authorization': 'Token ' + args.api})
            result.append(response.json())
        time.sleep(1)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
