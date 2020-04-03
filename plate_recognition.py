#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import collections
import csv
import json
import math
import time
from collections import OrderedDict
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter


def parse_arguments(args_hook=lambda _: _):
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from images and output the result as JSON.',
        epilog='Examples:\n'
        'To send images to our cloud service: '
        'python plate_recognition.py --api-key MY_API_KEY /path/to/vehicle-*.jpg\n',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '--api-key', help='Your API key.', required=False)
    parser.add_argument(
        '-r',
        '--regions',
        help='Match the license plate pattern fo specific region',
        required=False,
        action="append")
    parser.add_argument(
        '-s',
        '--sdk-url',
        help="Url to self hosted sdk  For example, http://localhost:8080",
        required=False)
    parser.add_argument('--camera-id',
                        help="Name of the source camera.",
                        required=False)

    parser.add_argument(
        '--mmc',
        action='store_true',
        help='Predict vehicle make and model (SDK only). It has to be enabled.')
    parser.add_argument('files', nargs='+', help='Path to vehicle images')
    args_hook(parser)
    args = parser.parse_args()
    if not args.sdk_url and not args.api_key:
        raise Exception('api-key is required')
    return args


def recognition_api(fp,
                    regions=[],
                    api_key=None,
                    sdk_url=None,
                    config={},
                    camera_id=None,
                    timestamp=None,
                    mmc=None):
    data = dict(regions=regions, config=json.dumps(config))
    if camera_id:
        data['camera_id'] = camera_id
    if mmc:
        data['mmc'] = mmc
    if timestamp:
        data['timestamp'] = timestamp
    if sdk_url:
        response = requests.post(sdk_url + '/alpr',
                                 files=dict(upload=fp),
                                 data=data)
    else:
        for _ in range(3):
            fp.seek(0)
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                files=dict(upload=fp),
                data=data,
                headers={'Authorization': 'Token ' + api_key})
            if response.status_code == 429:  # Max calls per second reached
                time.sleep(1)
            else:
                break
    if response.status_code < 200 or response.status_code > 300:
        print(response.text)
        exit(1)
    return response.json(object_pairs_hook=OrderedDict)


def blur(im, blur_amount, api_res):
    for res in api_res.get('results', []):
        b = res['box']
        width, height = b['xmax'] - b['xmin'], b['ymax'] - b['ymin']

        # Decrease padding size for large bounding boxes
        padding_x = int(max(0, width * (.3 * math.exp(-10 * width / im.width))))
        padding_y = int(
            max(0, height * (.3 * math.exp(-10 * height / im.height))))
        crop_box = (b['xmin'] - padding_x, b['ymin'] - padding_y,
                    b['xmax'] + padding_x, b['ymax'] + padding_y)
        ic = im.crop(crop_box)

        # Increase amount of blur with size of bounding box
        blur_image = ic.filter(
            ImageFilter.GaussianBlur(radius=math.sqrt(width * height) * .3 *
                                     blur_amount / 10))
        im.paste(blur_image, crop_box)
    return im


def draw_bb(im, data):
    draw = ImageDraw.Draw(im)
    for result in data:
        b = result['box']
        draw.rectangle(((b['xmin'], b['ymin']), (b['xmax'], b['ymax'])),
                       (0, 255, 0))
    im = im.resize((1920, 1050))
    return im


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            if isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
    return dict(items)


def flatten(result):
    plates = result['results']
    del result['results']
    del result['usage']
    if not plates:
        return result
    for plate in plates:
        data = result.copy()
        data.update(flatten_dict(plate))
    return data


def save_results(results, args):
    path = Path(args.output_file)
    if not path.parent.exists():
        print('%s does not exist' % path)
        return
    if not results:
        return
    if args.format == 'json':
        with open(path, 'w') as fp:
            json.dump(results, fp)
    elif args.format == 'csv':
        fieldnames = []
        for result in results[:10]:
            candidate = flatten(result.copy()).keys()
            if len(fieldnames) < len(candidate):
                fieldnames = candidate
        with open(path, 'w') as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                writer.writerow(flatten(result))


def custom_args(parser):
    parser.epilog += 'To blur images: python plate_recognition.py --sdk-url http://localhost:8080 --blur-amount 4 --blur-plates /path/to/vehicle-*.jpg\n'
    parser.epilog += 'To save results: python plate_recognition.py --sdk-url http://localhost:8080 -o data.csv --format csv /path/to/vehicle-*.jpg\n'
    parser.add_argument('-o', '--output-file', help='Save result to file.')
    parser.add_argument('--format',
                        help='Format of the result.',
                        default='json',
                        choices='json csv'.split())
    parser.add_argument(
        '--blur-amount',
        help=
        'Amount of blurring to apply on the license plates. Goes from 0 (no blur) to 10. Defaults to 5. ',
        default=5,
        type=float,
        required=False)
    parser.add_argument(
        '--blur-plates',
        action='store_true',
        help='Blur license plates and save image in filename_blurred.jpg.',
        required=False)


def main():
    args = parse_arguments(custom_args)
    paths = args.files

    results = []
    for path in paths:
        with open(path, 'rb') as fp:
            api_res = recognition_api(fp,
                                      args.regions,
                                      args.api_key,
                                      args.sdk_url,
                                      camera_id=args.camera_id,
                                      mmc=args.mmc)
        if args.blur_plates:
            im = blur(Image.open(path), args.blur_amount, api_res)
            filename = Path(path)
            im.save(filename.parent / ('%s_blurred%s' %
                                       (filename.stem, filename.suffix)))

        results.append(api_res)
    if args.output_file:
        save_results(results, args)
    else:
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
