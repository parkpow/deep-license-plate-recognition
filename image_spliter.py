#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import io
import os
import requests
import time
import image_slicer  # pip install image_slicer


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from a RTSP stream and save the result in a CSV file.',
        epilog=
        'For example: python image_spliter.py --api-key <API-TOKEN> --parts 4 /PATH/TO/highres.jpg'
    )
    parser.add_argument('--parts',
                        help='Number of parts. idealy even number',
                        required=True)
    parser.add_argument('--api-key', help='Your API key.', required=True)
    parser.add_argument('--camera-id', help='Unique Camera Id.', required=False)
    parser.add_argument(
        '--regions',
        help='Regions http://docs.platerecognizer.com/#regions-supported.',
        required=False)
    parser.add_argument(
        '--sdk-url',
        help="Url to self hosted sdk  For example, http://localhost:8080",
        required=False)
    parser.add_argument('files', nargs='+', help='Path to vehicle images')
    return parser.parse_args()


def main():
    args = parse_arguments()
    paths = args.files
    regions = args.regions
    parts = int(args.parts)
    camera_id = args.camera_id

    if not args.sdk_url and not args.api_key:
        raise Exception('api-key is required')
    if len(paths) == 0:
        print('File {} does not exist.'.format(args.FILE))
        return

    for path in paths:
        image_results = {}
        results = []
        tiles = image_slicer.slice(path, parts, save=False)
        for ind, tile in enumerate(tiles):
            image = io.BytesIO()
            filename, ext = os.path.splitext(path)
            if 'png' in ext.lower():
                ext = "PNG"
            else:
                ext = "JPEG"
            tile.image.save(image, ext)
            image.seek(0)
            if args.sdk_url:
                response = requests.post(args.sdk_url + '/alpr',
                                         files=dict(upload=image),
                                         data=dict(regions=regions,
                                                   camera_id=camera_id))
            else:
                response = requests.post(
                    'https://api.platerecognizer.com/v1/plate-reader/',
                    files=dict(upload=image),
                    data=dict(regions=regions, camera_id=camera_id),
                    headers={'Authorization': 'Token ' + args.api_key})

                if response.status_code == 429:  # Max calls per second reached
                    time.sleep(1)

            results.append((tile, response.json()))

        image_results["processing_time"] = sum(
            [result[1]['processing_time'] for result in results])

        for result in results:
            coordinates = result[0].coords
            if result[1]['results']:
                lp_results = result[1]['results']
                image_results['results'] = []
                for lp_result in lp_results:
                    lp_result['box'] = dict(
                        ymin=lp_result['box']["ymin"] + coordinates[1],
                        xmin=lp_result['box']["xmin"] + coordinates[0],
                        ymax=lp_result['box']["ymax"] + coordinates[1],
                        xmax=lp_result['box']["xmax"] + coordinates[0],
                    )
                    vehicle_box = lp_result['vehicle']["box"]
                    lp_result['vehicle']["box"] = dict(
                        ymin=vehicle_box["ymin"] + coordinates[1],
                        xmin=vehicle_box["xmin"] + coordinates[0],
                        ymax=vehicle_box["ymax"] + coordinates[1],
                        xmax=vehicle_box["xmax"] + coordinates[0],
                    )
                    image_results['results'].append(lp_result)

        print(image_results)  # result for whole


if __name__ == "__main__":
    main()
