import io
import json
import math
from itertools import combinations
from pathlib import Path

from PIL import Image

from plate_recognition import blur, draw_bb, parse_arguments, recognition_api


def bb_iou(a, b):
    # determine the (x, y)-coordinates of the intersection rectangle
    x_a = max(a["xmin"], b["xmin"])
    y_a = max(a["ymin"], b["ymin"])
    x_b = min(a["xmax"], b["xmax"])
    y_b = min(a["ymax"], b["ymax"])

    # compute the area of both the prediction and ground-truth
    # rectangles
    area_a = (a["xmax"] - a["xmin"]) * (a["ymax"] - a["ymin"])
    area_b = (b["xmax"] - b["xmin"]) * (b["ymax"] - b["ymin"])

    # compute the area of intersection rectangle
    area_inter = max(0, x_b - x_a) * max(0, y_b - y_a)
    return area_inter / float(max(area_a + area_b - area_inter, 1))


def clean_objs(objects, threshold=.1):
    # Only keep the ones with best score or no overlap
    for o1, o2 in combinations(objects, 2):
        if 'remove' in o1 or 'remove' in o2 or bb_iou(o1['box'],
                                                      o2['box']) <= threshold:
            continue
        if o1['score'] > o2['score']:
            o2['remove'] = True
        else:
            o1['remove'] = True
    return [x for x in objects if 'remove' not in x]


def merge_results(images):
    result = dict(results=[])
    for data in images:
        for item in data['prediction']['results']:
            result['results'].append(item)
            for b in [item['box'], item['vehicle'].get("box", {})]:
                b['ymin'] += data['y']
                b['xmin'] += data['x']
                b['ymax'] += data['y']
                b['xmax'] += data['x']
    result['results'] = clean_objs(result['results'])
    return result


def inside(a, b):
    return (a["xmin"] > b["xmin"] and a["ymin"] > b["ymin"] and
            a["xmax"] < b["xmax"] and a["ymax"] < b["ymax"])


def post_processing(results):
    new_list = []
    for item in results['results']:
        if item['score'] < .2 and any([
                inside(x['box'], item['box'])
                for x in results['results']
                if x != item
        ]):
            continue
        new_list.append(item)
    results['results'] = new_list
    return results


def process_image(path, args, i):
    config = dict(threshold_d=args.detection_threshold,
                  threshold_o=args.ocr_threshold,
                  mode='redaction')

    # Predictions
    source_im = Image.open(path)
    if source_im.mode != 'RGB':
        source_im = source_im.convert('RGB')
    images = [((0, 0), source_im)]  # Entire image
    # Top left and top right crops
    if args.split_image:
        y = 0
        win_size = .55
        width, height = source_im.width * win_size, source_im.height * win_size
        for x in [0, int((1 - win_size) * source_im.width)]:
            images.append(((x, y), source_im.crop(
                (x, y, x + width, y + height))))

    # Inference
    results = []
    for (x, y), im in images:
        im_bytes = io.BytesIO()
        im.save(im_bytes, 'JPEG', quality=95)
        im_bytes.seek(0)
        im_results = recognition_api(im_bytes,
                                     args.regions,
                                     args.api_key,
                                     args.sdk_url,
                                     config=config)
        results.append(dict(prediction=im_results, x=x, y=y))
    results = post_processing(merge_results(results))
    results['filename'] = Path(path).name

    # Set bounding box padding
    for item in results['results']:
        # Decrease padding size for large bounding boxes
        b = item['box']
        width, height = b['xmax'] - b['xmin'], b['ymax'] - b['ymin']
        padding_x = int(
            max(0, width * (.3 * math.exp(-10 * width / source_im.width))))
        padding_y = int(
            max(0, height * (.3 * math.exp(-10 * height / source_im.height))))
        b['xmin'] = b['xmin'] - padding_x
        b['ymin'] = b['ymin'] - padding_y
        b['xmax'] = b['xmax'] + padding_x
        b['ymax'] = b['ymax'] + padding_y

    if args.show_boxes or args.save_blurred:
        im = blur(source_im, 5, results)
        if args.show_boxes:
            im.show()
        if args.save_blurred:
            filename = Path(path)
            im.save(filename.parent / ('%s_blurred%s' %
                                       (filename.stem, filename.suffix)))
    if 0:
        draw_bb(source_im, results['results']).show()
    return results


def custom_args(parser):
    parser.epilog += 'To analyse the image for redaction: python number_plate_redaction.py  --api-key MY_API_KEY --split-image /tmp/car.jpg'
    parser.add_argument(
        '--split-image',
        action='store_true',
        help=
        'Do extra lookups on parts of the image. Useful on high resolution images.'
    )
    parser.add_argument('--show-boxes',
                        action='store_true',
                        help='Display the resulting blurred image.')
    parser.add_argument(
        '--save-blurred',
        action='store_true',
        help='Blur license plates and save image in filename_blurred.jpg.')
    parser.add_argument(
        '--detection-threshold',
        type=float,
        default=.2,
        help='Keep all detections above this threshold. Between 0 and 1.')
    parser.add_argument(
        '--ocr-threshold',
        type=float,
        default=.5,
        help=
        'Keep all plates if the characters reading score is above this threshold. Between 0 and 1.'
    )


def main():
    args = parse_arguments(custom_args)
    result = []
    for i, path in enumerate(args.files):
        if Path(path).is_file():
            result.append(process_image(path, args, i))
    if 0:
        for im_result in result:
            for i, x in enumerate(im_result['results']):
                im_result['results'][i] = dict(dscore=x['dscore'],
                                               score=x['score'],
                                               box=x['box'])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
