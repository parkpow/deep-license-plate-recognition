import io
import json

from PIL import Image

from number_plate_redaction import merge_results
from plate_recognition import draw_bb, parse_arguments, recognition_api

CAMERA_OPTIONS = dict(
    front=dict(rotation=90, crop_bottom=.8, crop_top=.35),
    front_left=dict(rotation=-90, crop_bottom=.8, crop_top=.4),
    front_right=dict(rotation=-90, crop_bottom=.8, crop_top=.35),
    back_left=dict(rotation=90, crop_bottom=.8, crop_top=.4),
    back_right=dict(rotation=90, crop_bottom=.9, crop_top=.4),
)


def camera_args(parser):
    parser.epilog += 'To process panoramic images: python cowi_images.py  --api-key MY_API_KEY --camera front /tmp/car.jpg'
    parser.add_argument('--camera',
                        required=True,
                        choices=CAMERA_OPTIONS.keys())


def rotate_bb(box, rotation, size):
    if rotation == 90:
        return dict(xmin=size[1] - box['ymin'],
                    xmax=size[1] - box['ymax'],
                    ymin=box['xmin'],
                    ymax=box['xmax'])
    elif rotation == -90:
        return dict(xmin=box['ymin'],
                    xmax=box['ymax'],
                    ymin=size[0] - box['xmin'],
                    ymax=size[0] - box['xmax'])


def process_image(path, args):
    options = CAMERA_OPTIONS[args.camera]
    config = dict(threshold_d=.2, threshold_o=.3, mode='redaction')

    # Pre process image
    source_im = Image.open(path)
    rotated = source_im.rotate(options['rotation'], expand=True)
    top = rotated.height * options['crop_top']
    bottom = rotated.height * options['crop_bottom']
    api_im = rotated.crop((0, top, rotated.width, bottom))

    # Predictions
    images = [((0, 0), api_im)]  # Entire image
    # Top left and top right crops
    y = 0
    win_size = .55
    width, height = api_im.width * win_size, api_im.height * win_size
    for x in [0, (1 - win_size) * api_im.width]:
        images.append(((x, y), api_im.crop((x, y, x + width, y + height))))

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
    results = merge_results(results)

    # Update bounding boxes
    for lp in results['results']:
        box = lp['box']
        box['ymin'] += top
        box['ymax'] += top
        # Rotate
        lp['box'] = rotate_bb(box, options['rotation'], rotated.size)

    if 0:
        draw_bb(source_im, results['results']).show()
    return results


def main():
    args = parse_arguments(camera_args)
    result = []
    for path in args.files:
        result.append(process_image(path, args))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
