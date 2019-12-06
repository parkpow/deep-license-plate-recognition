#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import json
import time
from collections import OrderedDict

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from images and output the result as JSON.',
        epilog=
        'For example: python plate_recognition.py --api-key MY_API_KEY "/path/to/vehicle-*.jpg"'
    )
    parser.add_argument('--api-key', help='Your API key.', required=False)
    parser.add_argument(
        '--regions',
        help='Match the license plate pattern fo specific region',
        required=False,
        action="append")
    parser.add_argument(
        '--sdk-url',
        help="Url to self hosted sdk  For example, http://localhost:8080",
        required=False)
    parser.add_argument('files', nargs='+', help='Path to vehicle images')
    return parser.parse_args()


def main():
    args = parse_arguments()
    result = []
    paths = args.files
    regions = args.regions

    if not args.sdk_url and not args.api_key:
        raise Exception('api-key is required')
    if len(paths) == 0:
        print('File {} does not exist.'.format(args.FILE))
        return
    for path in paths:
        with open(path, 'rb') as fp:
            if args.sdk_url:
                response = requests.post(args.sdk_url + '/alpr',
                                         files=dict(upload=fp),
                                         data=dict(regions=regions))
            else:
                for _ in range(3):
                    response = requests.post(
                        'https://api.platerecognizer.com/v1/plate-reader/',
                        files=dict(upload=fp),
                        data=dict(regions=regions),
                        headers={'Authorization': 'Token ' + args.api_key})
                    if response.status_code == 429:  # Max calls per second reached
                        time.sleep(1)
                    else:
                        break
            result.append(response.json(object_pairs_hook=OrderedDict))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
