#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import json
import math
import os
import time
from collections import OrderedDict

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
    args_hook(parser)
    args = parser.parse_args()
    if not args.sdk_url and not args.api_key:
        raise Exception('api-key is required')
    return args


def recognition_api(fp, regions, api_key=None, sdk_url=None, config={}):
    data = dict(regions=regions, config=json.dumps(config))
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
    return response.json(object_pairs_hook=OrderedDict)


def blur(args, path, api_res):
    im = Image.open(path)
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
        blur_amount = math.sqrt(width * height) * .2 * args.blur_amount / 10
        blur_image = ic.filter(ImageFilter.GaussianBlur(radius=blur_amount))
        im.paste(blur_image, crop_box)
    filename = os.path.basename(path)
    blurred_image_path = os.path.join(args.blur_dir, filename)
    im.save(blurred_image_path)


def draw_bb(im, data):
    draw = ImageDraw.Draw(im)
    for result in data:
        b = result['box']
        draw.rectangle(((b['xmin'], b['ymin']), (b['xmax'], b['ymax'])),
                       (0, 255, 0))
    im = im.resize((1920, 1050))
    return im


def blurring_args(parser):
    parser.epilog += 'To blur images: python plate_recognition.py  --sdk-url http://localhost:8080 --blur-amount 4 --blur-dir /path/save/blurred/images /path/to/vehicle-*.jpg'
    parser.add_argument(
        '--blur-amount',
        help=
        'Amount of blurring to apply on the license plates. Goes from 0 (no blur) to 10. Defaults to 5. ',
        default=5,
        type=float,
        required=False)
    parser.add_argument(
        '--blur-dir',
        help='Path to the directory where blurred images are saved.',
        required=False)


def main():
    args = parse_arguments(blurring_args)
    paths = args.files

    if args.blur_dir and not os.path.exists(args.blur_dir):
        print('{} does not exist'.format(args.blur_dir))
        return

    result = []
    for path in paths:
        with open(path, 'rb') as fp:
            api_res = recognition_api(fp, args.regions, args.api_key,
                                      args.sdk_url)
        if args.blur_dir:
            blur(args, path, api_res)
        result.append(api_res)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
