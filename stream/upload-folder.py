import argparse
from pathlib import Path
import requests
import os
import sys
import logging

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


def stream_api(i, args):
    if args.mask:
        data = dict(mask_id=args.mask)
    else:
        data = None

    with open(i, 'rb') as fp:
        while True:
            response = requests.post(args.sdk_url,
                                     files=dict(upload=fp),
                                     data=data)

            if response.status_code < 200 or response.status_code > 300:
                logging.error(response.text)
                return None
            else:
                res_json = response.json()
                if 'error' in res_json:
                    logging.error(response.text)
                    return None

                return res_json


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f',
                        '--folder',
                        required=True,
                        help='Folder containing videos to process.')

    parser.add_argument("-m",
                        "--mask",
                        type=str,
                        help="Camera Mask ID to use in the recognition.")

    parser.add_argument(
        '-s',
        '--sdk-url',
        default='http://localhost:8081',
        help="Url to Stream File Upload Server http://localhost:8081")

    args = parser.parse_args()

    # Process files in folder
    videos_directory = Path(args.folder)

    for file in videos_directory.iterdir():
        if file.is_dir():
            continue
        logging.info(f'Processing file: {file}')
        results = stream_api(file, args)
        logging.info(f'Results:{results}')
