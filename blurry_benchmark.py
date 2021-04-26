import math
import io
import os
import imghdr
import argparse

from PIL import Image, ImageFilter
from plate_recognition import recognition_api


def process(buffer, api_key, sdk_url):
    plates = []
    run_recognition_response = recognition_api(buffer,
                                               api_key=api_key,
                                               sdk_url=sdk_url)
    for result in run_recognition_response['results']:
        plate = result['plate']
        plates.append(plate)

    print(f'Plates: {plates}')
    return plates


def similar(old, new):
    return set(old) == set(new)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Blurry Benchmark',
        epilog='Examples:\n'
        'Benchmark Blurry effect on recognition\n',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '--api-key', help='Your API key.', required=False)

    parser.add_argument(
        '-s',
        '--sdk-url',
        help="Url to self hosted sdk  For example, http://localhost:8080",
        required=False)

    parser.add_argument('-d',
                        '--root-dir',
                        help='Specify folder with images.',
                        required=True)

    args = parser.parse_args()
    if not args.sdk_url and not args.api_key:
        raise Exception('api-key is required')

    return args


def main():
    args = parse_arguments()

    # loop folders recursively
    for subdir, dirs, files in os.walk(args.root_dir):
        for file in files:
            image_file_path = os.path.join(subdir, file)

            img_type = imghdr.what(image_file_path)

            if img_type:
                print(f'Processing image: {image_file_path}')
                initial_plates = None

                image = Image.open(image_file_path)
                width, height = image.size

                for blur_amount in range(10):
                    print(f"Blur Amount: {blur_amount}")
                    if initial_plates:
                        image = image.filter(
                            ImageFilter.GaussianBlur(
                                radius=math.sqrt(width * height) * .3 *
                                blur_amount / 10))

                    buffer = io.BytesIO()
                    image.save(buffer, 'PPM')  # PPM does no compression
                    buffer.seek(0)

                    new_plates = process(buffer, args.api_key, args.sdk_url)

                    if initial_plates:
                        if not similar(initial_plates, new_plates):
                            print(
                                f'Text change detected at blur amount: [{blur_amount}]'
                            )
                            break
                    else:
                        if len(new_plates) == 0:
                            print("No plates detected in image")
                            break
                        initial_plates = new_plates.copy()


if __name__ == '__main__':
    main()
