import logging
import os
import sys
import time
from pathlib import Path

import cv2
import requests
from configobj import ConfigObj
from utils import draw_bounding_box_on_image
import numpy as np

LOG_LEVEL = os.environ.get('LOGGING', 'INFO').upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style='{',
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)

BASE_WORKING_DIR = '/user-data/'

CONFIG_FILE = f'{BASE_WORKING_DIR}config.ini'


def recognition_api(cv2_frame, data, sdk_url, api_key):
    retval, buffer = cv2.imencode('.jpg', cv2_frame)

    if sdk_url:
        url = sdk_url + '/v1/plate-reader/'
        headers = None
    else:
        if api_key is None:
            raise Exception('A TOKEN is required if using Cloud API')

        url = 'https://api.platerecognizer.com/v1/plate-reader/'
        headers = {'Authorization': 'Token ' + api_key}

    while True:
        response = requests.post(
            url, files=dict(upload=buffer), headers=headers, data=data
        )

        if response.status_code < 200 or response.status_code > 300:
            if response.status_code == 429:
                time.sleep(1)
            else:
                logging.error(response.text)
                raise Exception('Error running recognition')
        else:
            res_json = response.json()
            if 'error' in res_json:
                logging.error(response.text)
                raise Exception('Error running recognition')

            return res_json


def visualize_frame(cv2_frame, sdk_url, snapshot_api_token):
    run_recognition_response = recognition_api(
        cv2_frame, {}, sdk_url, snapshot_api_token
    )

    for result in run_recognition_response['results']:
        plate_bounding_box = result['box']
        plate = result['plate']
        draw_bounding_box_on_image(
            cv2_frame,
            plate_bounding_box['ymin'],
            plate_bounding_box['xmin'],
            plate_bounding_box['ymax'],
            plate_bounding_box['xmax'],
            plate,
        )

        # Vehicle box
        if result['vehicle']['score'] > 0:
            vehicle_bounding_box = result['vehicle']['box']
            vehicle = result['vehicle']['type']
            draw_bounding_box_on_image(
                cv2_frame,
                vehicle_bounding_box['ymin'],
                vehicle_bounding_box['xmin'],
                vehicle_bounding_box['ymax'],
                vehicle_bounding_box['xmax'],
                vehicle,
            )

    return cv2_frame


def blur_api(cv2_frame, blur_url):
    retval, buffer = cv2.imencode('.jpg', cv2_frame)

    response = requests.post(blur_url, files=dict(upload=('frame.jpg', buffer)))
    if response.status_code < 200 or response.status_code > 300:
        logging.error(response.text)
        raise Exception('Error performing blur')
    else:
        return response


def blur_frame(cv2_frame, blur_url):
    blur_response = blur_api(cv2_frame, blur_url)
    arr = np.asarray(bytearray(blur_response.content), dtype=np.uint8)
    blurred_frame = cv2.imdecode(arr, -1)  # 'Load it as it is'

    return blurred_frame


def save_frame(count, cv2_image, save_dir, image_format='jpg'):
    save_path = f'{save_dir}frame_{count}.{image_format}'
    lgr.debug(f'saving frame to: {save_path}')
    if image_format == 'png':
        # default 3, 9 is highest compression
        cv2.imwrite(save_path, cv2_image, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])

    elif image_format == 'jpg':
        # default 95, 100 is best quality
        cv2.imwrite(save_path, cv2_image, [cv2.IMWRITE_JPEG_QUALITY, 95])

    else:
        raise Exception(f'Unrecognized Output format: {image_format}')


def init_writer(filename, cap):
    fps = cap.get(cv2.CAP_PROP_FPS)
    lgr.debug(f"Frames per second using video.get(cv2.CAP_PROP_FPS) : {fps}")

    # Retrieve Default Resolution from camera
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))

    # Define the codec and create VideoWriter object.
    return cv2.VideoWriter(
        filename,
        cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
        fps,
        (frame_width, frame_height),
    )


def process_camera(camera_id, camera_config):
    lgr.debug(f'Processing camera: {camera_id}')
    lgr.debug(f'camera_config: {camera_config}')
    if camera_config['active'] != 'yes':
        lgr.debug('skipped inactive camera')
        return

    url = camera_config['url']

    # check processing actions for camera
    enabled_actions = camera_config.sections
    lgr.debug(f'enabled_actions: {enabled_actions}')

    frames_enabled = 'frames' in enabled_actions
    visualization_enabled = 'visualization' in enabled_actions
    blur_enabled = 'blur' in enabled_actions

    lgr.debug(f'CONFIG frames_enabled: {frames_enabled}')
    lgr.debug(f'CONFIG visualization_enabled: {visualization_enabled}')
    lgr.debug(f'CONFIG blur_enabled: {blur_enabled}')

    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        lgr.debug("Error opening video stream or file")
        exit(1)

    if visualization_enabled:
        output1_filename = f'{BASE_WORKING_DIR}{camera_id}_visualization.avi'
        out1 = init_writer(output1_filename, cap)
    else:
        out1 = None

    if blur_enabled:
        output2_filename = f'{BASE_WORKING_DIR}{camera_id}_blur.avi'
        out2 = init_writer(output2_filename, cap)
    else:
        out2 = None

    # Create the output dir for frames if missing
    if frames_enabled:
        frames_output_dir = f'{BASE_WORKING_DIR}{camera_id}_frames/'
        Path(frames_output_dir).mkdir(parents=True, exist_ok=True)
    else:
        frames_output_dir = None

    lgr.debug(f'CONFIG frames_output_dir: {frames_output_dir}')

    # Parse visualization parameters
    if visualization_enabled:
        visualization = camera_config['visualization']
        sdk_url = visualization.get('sdk_url', None)
        snapshot_api_token = visualization.get('token', None)
    else:
        sdk_url = None
        snapshot_api_token = None

    lgr.debug(f'CONFIG sdk_url: {sdk_url}')
    lgr.debug(f'CONFIG snapshot_api_token: {snapshot_api_token}')

    # Parse blur parameters
    if blur_enabled:
        blur = camera_config['blur']
        blur_url = blur.get('blur_url', None)
    else:
        blur_url = None

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            lgr.debug(f'Processing frame: {frame_count}')
            frame_count += 1

            if frames_enabled:
                save_frame(frame_count, frame, frames_output_dir)

            if visualization_enabled:
                # adding filled rectangle on each frame
                visualized_frame = visualize_frame(frame, sdk_url, snapshot_api_token)
                out1.write(visualized_frame)

            if blur_enabled:
                # Blurring each frame
                blurred_frame = blur_frame(frame, blur_url)
                out2.write(blurred_frame)

        else:
            break

    cap.release()
    if out1:
        out1.release()
    if out2:
        out2.release()


def main():
    if not os.path.exists(CONFIG_FILE):
        lgr.error('config.ini not found, did you forget to mount the stream volume?')
        exit(1)

    config = ConfigObj(CONFIG_FILE)
    cameras = config['cameras']
    camera_ids = cameras.sections

    for camera_id in camera_ids:
        camera_config = cameras[camera_id]
        process_camera(camera_id, camera_config)


if __name__ == "__main__":
    main()
