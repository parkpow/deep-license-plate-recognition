#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import json
from collections import OrderedDict
from glob import glob

import requests


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from images and output the result as JSON.')
    parser.add_argument('FILE', help='Path to vehicle image or pattern.')
    parser.add_argument('--url', default='http://localhost:8080')
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
            response = requests.post(args.url + '/alpr', files=dict(upload=fp))
            result.append(response.json(object_pairs_hook=OrderedDict))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
