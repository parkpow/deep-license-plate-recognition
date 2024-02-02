import logging
import os
import sys
import tempfile
import time
from pathlib import Path

import cv2
import ffmpegcv
import numpy as np
import requests
from flask import Flask, jsonify, request
from interpolator import Interpolator
from utils import draw_bounding_box_on_image

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(levelname)-5s  [%(name)s.%(lineno)d] => %(message)s",
)

lgr = logging.getLogger("video-editor")

BASE_WORKING_DIR = "/user-data/"


def recognition_api(cv2_frame, data, sdk_url, api_key):
    retval, buffer = cv2.imencode(".jpg", cv2_frame)

    if sdk_url:
        url = sdk_url + "/v1/plate-reader/"
        headers = None
    else:
        if api_key is None:
            raise Exception("A TOKEN is required if using Cloud API")

        url = "https://api.platerecognizer.com/v1/plate-reader/"
        headers = {"Authorization": "Token " + api_key}

    while True:
        response = requests.post(
            url, files=dict(upload=buffer), headers=headers, data=data
        )

        if response.status_code < 200 or response.status_code > 300:
            if response.status_code == 429:
                time.sleep(1)
            else:
                logging.error(response.text)
                raise Exception("Error running recognition")
        else:
            res_json = response.json()
            if "error" in res_json:
                logging.error(response.text)
                raise Exception("Error running recognition")

            return res_json


def visualize_frame(cv2_frame, sdk_url, snapshot_api_token):
    run_recognition_response = recognition_api(
        cv2_frame, {}, sdk_url, snapshot_api_token
    )

    for result in run_recognition_response["results"]:
        plate_bounding_box = result["box"]
        plate = result["plate"]
        draw_bounding_box_on_image(
            cv2_frame,
            plate_bounding_box["ymin"],
            plate_bounding_box["xmin"],
            plate_bounding_box["ymax"],
            plate_bounding_box["xmax"],
            plate,
        )

        # Vehicle box
        if result["vehicle"]["score"] > 0:
            vehicle_bounding_box = result["vehicle"]["box"]
            vehicle = result["vehicle"]["type"]
            draw_bounding_box_on_image(
                cv2_frame,
                vehicle_bounding_box["ymin"],
                vehicle_bounding_box["xmin"],
                vehicle_bounding_box["ymax"],
                vehicle_bounding_box["xmax"],
                vehicle,
            )

    return cv2_frame


def blur_api(cv2_frame, blur_url):
    retval, buffer = cv2.imencode(".jpg", cv2_frame)

    response = requests.post(blur_url, files=dict(upload=("frame.jpg", buffer)))
    if response.status_code < 200 or response.status_code > 300:
        logging.error(response.text)
        raise Exception("Error performing blur")
    else:
        return response


def get_blur_polygons(cv2_frame: np.ndarray, blur_url: str):
    """
    Call Blur API to request polygons to be blurred.
    """
    blur_response = blur_api(cv2_frame, blur_url)
    polygons = [
        np.array(plate["polygon"], dtype=np.float32)
        for plate in blur_response.json()["plates"]
    ]

    return polygons


def save_frame(count, cv2_image, save_dir, image_format="jpg"):
    save_path = f"{save_dir}frame_{count}.{image_format}"
    lgr.debug(f"saving frame to: {save_path}")
    if image_format == "png":
        # default 3, 9 is highest compression
        cv2.imwrite(save_path, cv2_image, [int(cv2.IMWRITE_PNG_COMPRESSION), 3])

    elif image_format == "jpg":
        # default 95, 100 is best quality
        cv2.imwrite(save_path, cv2_image, [cv2.IMWRITE_JPEG_QUALITY, 95])

    else:
        raise Exception(f"Unrecognized Output format: {image_format}")


def init_writer(filename, fps):
    return ffmpegcv.noblock(ffmpegcv.VideoWriter, filename, "h264", fps)


def process_video(video, action):
    filename = video.filename
    lgr.debug(f"Processing video: {filename}")

    # check processing actions for camera
    lgr.debug(f"enabled_actions: {action}")

    frames_enabled = "frames" in action
    visualization_enabled = "visualization" in action
    blur_enabled = "blur" in action

    lgr.debug(f"CONFIG frames_enabled: {frames_enabled}")
    lgr.debug(f"CONFIG visualization_enabled: {visualization_enabled}")
    lgr.debug(f"CONFIG blur_enabled: {blur_enabled}")

    out1, out2, frames_output_dir, sdk_url, snapshot_api_token, blur_url = (
        None,
        None,
        None,
        None,
        None,
        None,
    )

    temp_dir = tempfile.mkdtemp()

    # Save the uploaded video file to the temporary directory
    video_path = os.path.join(temp_dir, video.filename)
    video.save(video_path)

    cap = ffmpegcv.VideoCapture(video_path)

    if not cap.isOpened():
        lgr.debug("Error opening video stream or file")
        exit(1)

    filename_stem = Path(video_path).stem
    video_format_ext = "mp4"

    # Override FPS if provided
    try:
        fps = int(os.environ.get("FPS"))
    except TypeError:
        # ffmpegcv cap.fps is not reliable
        # Calculate FPS manually by counting frames for 500ms

        fps_cap = cv2.VideoCapture(video_path)
        frame_count = 0
        last_frame_time = 0
        while fps_cap.isOpened():
            ret, _ = fps_cap.read()
            last_frame_time = fps_cap.get(cv2.CAP_PROP_POS_MSEC)
            # Stop at half a second or no more frames
            if not ret or last_frame_time >= 500:
                break
            frame_count += 1
        fps_cap.release()
        assert last_frame_time > 0, "Video too short or frames are not readable"
        fps = frame_count * 1000 / last_frame_time
    lgr.debug(f"FPS: {fps}")

    if visualization_enabled:
        output1_filename = (
            f"{BASE_WORKING_DIR}{filename_stem}_visualization.{video_format_ext}"
        )
        out1 = init_writer(output1_filename, fps)

    if blur_enabled:
        output2_filename = f"{BASE_WORKING_DIR}{filename_stem}_blur.{video_format_ext}"
        out2 = init_writer(output2_filename, fps)

    # Create the output dir for frames if missing
    if frames_enabled:
        frames_output_dir = f"{BASE_WORKING_DIR}{filename_stem}_frames/"
        Path(frames_output_dir).mkdir(parents=True, exist_ok=True)
        lgr.debug(f"CONFIG frames_output_dir: {frames_output_dir}")

    # Parse visualization parameters
    if visualization_enabled:
        sdk_url = os.environ.get("SDK_URL")
        snapshot_api_token = os.environ.get("TOKEN")

        lgr.debug(f"CONFIG sdk_url: {sdk_url}")
        lgr.debug(f"CONFIG snapshot_api_token: {snapshot_api_token}")

    # Parse blur parameters
    if blur_enabled:
        blur_url = os.environ.get("BLUR_URL")

    try:
        sample_rate = int(os.environ.get("SAMPLE"))
    except Exception:
        sample_rate = 5
    keyframe_residue = 1 % sample_rate  # for sample_rate = 1
    interpolator = Interpolator(sample_rate, out2)
    interpolator.start()

    start = time.time()
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            lgr.debug(f"Processing frame: {frame_count}")
            frame_count += 1

            if frames_enabled:
                save_frame(frame_count, frame, frames_output_dir)

            if visualization_enabled:
                # adding filled rectangle on each frame
                visualized_frame = visualize_frame(frame, sdk_url, snapshot_api_token)
                out1.write(visualized_frame)

            if blur_enabled:
                if frame_count % sample_rate == keyframe_residue:
                    # Keyframe
                    polygons = get_blur_polygons(frame, blur_url)
                    interpolator.feed_keyframe(frame, frame_count, polygons)
                else:
                    # Skipframes
                    interpolator.feed_skipframe(frame)
        else:
            break

    # Flush the remaining skipframes
    if blur_enabled and interpolator.is_flush_needed(frame_count):
        frame, _ = interpolator.frame_buffer.queue[-1]
        polygons = get_blur_polygons(frame, blur_url)
        interpolator.flush(frame_count, polygons)
    interpolator.close()

    cap.release()
    if out1:
        out1.release()
    if out2:
        out2.release()

    lgr.debug(f"Frame count: {frame_count}")
    lgr.debug(f"Time taken: {time.time() - start}")
    lgr.debug(f"Done processing video {filename}")
    os.remove(video_path)
    os.rmdir(temp_dir)


app = Flask(__name__)


@app.route("/process-video", methods=["POST"])
def process_video_route():
    if "upload" not in request.files or "action" not in request.form:
        return jsonify({"error": "Invalid request"}), 400

    file = request.files["upload"]
    action = request.form["action"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        process_video(file, action)
    except Exception as e:
        lgr.error("Error:", exc_info=e)
        return jsonify({"error": str(e)}), 500

    return jsonify("Done."), 200


app.run(host="0.0.0.0", port=8081, debug=True)
