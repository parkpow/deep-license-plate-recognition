import io

import numpy as np
from PIL import Image, ImageFilter

from plate_recognition import parse_arguments, recognition_api


def main():
    args = parse_arguments()
    scores = []
    for path in args.files:
        blur_amount = 0
        init_value = ''
        while True:
            # Blur image
            image = Image.open(path)
            if image.height > 1080:
                image = image.resize(
                    (int(image.width * 1080 / image.height), 1080))
            elif image.width > 1980:
                image = image.resize(
                    (1980, int(image.height * 1980 / image.width)))
            if blur_amount > 0:
                image = image.filter(
                    ImageFilter.GaussianBlur(radius=blur_amount))
            buffer = io.BytesIO()
            image.save(buffer, 'jpeg')
            buffer.seek(0)

            # Do prediction
            api_res = recognition_api(buffer,
                                      args.regions,
                                      args.api_key,
                                      args.sdk_url,
                                      camera_id=args.camera_id)
            if not init_value:
                init_value = api_res['results'][0]['plate']
            elif not api_res[
                    'results'] or init_value != api_res['results'][0]['plate']:
                break
            blur_amount += .5
        scores.append(blur_amount)
        print(path, blur_amount)
    print('Blur score', np.mean(scores))


if __name__ == "__main__":
    main()
