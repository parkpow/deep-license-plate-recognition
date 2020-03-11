import io
import json
from itertools import combinations

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


def process_image(path, args, i):
    config = dict(threshold_d=args.detection_threshold,
                  threshold_o=args.ocr_threshold,
                  mode='redaction')

    # Predictions
    source_im = Image.open(path)
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
        if im.mode == 'RGBA':
            im = im.convert('RGB')
        im.save(im_bytes, 'JPEG', quality=95)
        im_bytes.seek(0)
        im_results = recognition_api(im_bytes,
                                     args.regions,
                                     args.api_key,
                                     args.sdk_url,
                                     config=config)
        results.append(dict(prediction=im_results, x=x, y=y))
    results = merge_results(results)

    if args.show_boxes:
        blur(source_im, 5, results).show()
    if 0:
        draw_bb(source_im, results['results']).show()
    return results


def custom_args(parser):
    parser.epilog += 'To analyse the image for redaction: python number_plate_redaction.py  --api-key MY_API_KEY --split-image /tmp/car.jpg'
    parser.add_argument('--split-image', action='store_true', help='')
    parser.add_argument('--show-boxes', action='store_true')
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
        result.append(process_image(path, args, i))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
