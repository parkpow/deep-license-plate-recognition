#!/usr/bin/env python
from pprint import pprint
import argparse
import requests


def parse_arguments():
    parser = argparse.ArgumentParser(description='License plate recognition')
    parser.add_argument('--api', help='Your API key.', required=True)
    parser.add_argument('file', help='Vehicle image.')
    return parser.parse_args()


def main():
    args = parse_arguments()
    with open(args.file) as fp:
        response = requests.post(
            'https://platerecognizer.com/plate-reader/',
            files=dict(upload=fp),
            headers={'Authorization': 'Token ' + args.api})
    pprint(response.json())


if __name__ == '__main__':
    main()
