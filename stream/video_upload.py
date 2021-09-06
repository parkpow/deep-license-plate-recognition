import argparse
from pathlib import Path
import requests
import os
import sys
import logging
import json
from gooey import Gooey
from gooey import GooeyParser

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


def stream_api(image_path, args):
    if args.mask:
        data = dict(mask_id=args.mask)
    else:
        data = None

    with open(image_path, 'rb') as fp:
        response = requests.post(args.sdk_url, files=dict(upload=fp), data=data)
        if response.status_code < 200 or response.status_code > 300:
            logging.error(response.text)
            return None
        else:
            return response.json()


@Gooey(program_name='Videos Uploader')
def main():
    parser = GooeyParser(description="Upload Videos from a folder to Stream file-upload")
    parser.add_argument('folder',
                        help='Folder containing videos to process.',
                        widget='DirChooser')

    parser.add_argument("-m",
                        "--mask",
                        type=str,
                        help="Camera Mask ID to use in the recognition.")

    parser.add_argument(
        '-s',
        '--sdk-url',
        default='http://localhost:8081',
        help="Url to Stream File Upload Server")

    args = parser.parse_args()

    # Process files in folder
    videos_directory = Path(args.folder)
    with open('output.jsonl', 'a') as outfile:
        for file in videos_directory.iterdir():
            if file.is_dir():
                continue
            logging.info(f'Processing file: {file}')
            results = stream_api(file, args)
            logging.info(f'Results:{results}')
            if results:
                json.dump(results, outfile)
                outfile.write('\n')
                outfile.flush()

if __name__ == '__main__':
    main()
