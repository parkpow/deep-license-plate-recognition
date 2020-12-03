#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import argparse
import collections
import csv
import json
import math
import time
import re
from collections import OrderedDict
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont


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
        help='Match the license plate pattern of a specific region',
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
                    mmc=None,
                    exit_on_error=True):
    data = dict(regions=regions, config=json.dumps(config))
    if camera_id:
        data['camera_id'] = camera_id
    if mmc:
        data['mmc'] = mmc
    if timestamp:
        data['timestamp'] = timestamp
    response = None
    if sdk_url:
        fp.seek(0)
        response = requests.post(sdk_url + '/v1/plate-reader/',
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
    if not response:
        return {}
    if response.status_code < 200 or response.status_code > 300:
        print(response.text)
        if exit_on_error:
            exit(1)
    return response.json(object_pairs_hook=OrderedDict)


def blur(im, blur_amount, api_res, ignore_no_bb=False, ignore_list=None):
    for res in api_res.get('results', []):
        if ignore_no_bb and res['vehicle']['score'] == 0.0:
            continue

        if ignore_list:
            skip_blur = False
            for ignore_regex in ignore_list:
                if re.search(ignore_regex, res['plate']):
                    skip_blur = True
                    break
            if skip_blur:
                continue

        b = res['box']
        width, height = b['xmax'] - b['xmin'], b['ymax'] - b['ymin']
        crop_box = (b['xmin'], b['ymin'], b['xmax'], b['ymax'])
        ic = im.crop(crop_box)

        # Increase amount of blur with size of bounding box
        blur_image = ic.filter(
            ImageFilter.GaussianBlur(radius=math.sqrt(width * height) * .3 *
                                     blur_amount / 10))
        im.paste(blur_image, crop_box)
    return im


def draw_bb(im, data, new_size=(1920, 1050), text_func=None):
    draw = ImageDraw.Draw(im)
    font_path = Path('assets/DejaVuSansMono.ttf')
    if font_path.exists():
        font = ImageFont.truetype(str(font_path), 10)
    else:
        font = ImageFont.load_default()
    rect_color = (0, 255, 0)
    for result in data:
        b = result['box']
        coord = [(b['xmin'], b['ymin']), (b['xmax'], b['ymax'])]
        draw.rectangle(coord, outline=rect_color)
        draw.rectangle(((coord[0][0] - 1, coord[0][1] - 1),
                        (coord[1][0] - 1, coord[1][1] - 1)),
                       outline=rect_color)
        draw.rectangle(((coord[0][0] - 2, coord[0][1] - 2),
                        (coord[1][0] - 2, coord[1][1] - 2)),
                       outline=rect_color)
        if text_func:
            text = text_func(result)
            text_width, text_height = font.getsize(text)
            margin = math.ceil(0.05 * text_height)
            draw.rectangle(
                [(b['xmin'] - margin, b['ymin'] - text_height - 2 * margin),
                 (b['xmin'] + text_width + 2 * margin, b['ymin'])],
                fill='white')
            draw.text((b['xmin'] + margin, b['ymin'] - text_height - margin),
                      text,
                      fill='black',
                      font=font)

    if new_size:
        im = im.resize(new_size)
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
    parser.add_argument('--engine-config', help='Engine configuration.')
    parser.add_argument('-o', '--output-file', help='Save result to file.')
    parser.add_argument('--format',
                        help='Format of the result.',
                        default='json',
                        choices='json csv'.split())
    parser.add_argument(
        '--mmc',
        action='store_true',
        help='Predict vehicle make and model. Only available to paying users.')
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
    engine_config = {}
    if args.engine_config:
        try:
            json.loads(args.engine_config)
        except json.JSONDecodeError as e:
            print(e)
            return

    for path in paths:
        with open(path, 'rb') as fp:
            api_res = recognition_api(fp,
                                      args.regions,
                                      args.api_key,
                                      args.sdk_url,
                                      config=engine_config,
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
