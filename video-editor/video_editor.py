import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import cv2
import ffmpegcv
import numpy as np
import requests
from flask import Flask, jsonify, request
from utils import draw_bounding_box_on_image

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)

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
    # Request polygons
    blur_response = blur_api(cv2_frame, blur_url)
    polygons = [
        np.array(plate["polygon"], dtype=np.float32)
        for plate in blur_response.json()["plates"]
    ]

    # Calculate centers
    centers = np.empty((len(polygons), 2), dtype=np.float32)
    for i, poly in enumerate(polygons):
        centers[i] = np.mean(poly, axis=0)

    return polygons, centers


def blur_polygons(
    cv2_frame: np.ndarray, polygons: list[np.ndarray], blur_amount: int, writer: Any
):
    """
    Draws blurred polygons to the frame.
    """
    result = cv2_frame
    channel_count = cv2_frame.shape[2]
    ignore_mask_color = (255,) * channel_count

    for poly in polygons:
        polygon_height = abs(int(poly[3][1] - poly[0][1]))
        polygon_width = abs(int(poly[2][0] - poly[3][0]))

        # Prep mask
        mask = np.zeros(cv2_frame.shape, dtype=np.uint8)
        cv2.fillConvexPoly(mask, np.int32(poly), ignore_mask_color, cv2.LINE_AA)

        # Prep totally blurred image
        kernel_width = (polygon_width // blur_amount) | 1
        kernel_height = (polygon_height // blur_amount) | 1
        blurred_image = cv2.GaussianBlur(cv2_frame, (kernel_width, kernel_height), 0)

        # Combine original and blur
        result = cv2.bitwise_and(result, cv2.bitwise_not(mask)) + cv2.bitwise_and(
            blurred_image, mask
        )

    writer.write(result)


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


class FrameBuffer:
    """
    Stores frames in a ringbuffer.
    Provides useful methods for accessing frames.
    """

    def __init__(self, sample_rate: int):
        self.buffer = [
            (np.array([], dtype=np.uint8), np.array([], dtype=np.uint8))
            for _ in range(sample_rate)
        ]
        self.buffer_idx = 0

    def increment(self, steps: int = 1) -> None:
        """
        Moves index forward without changing the buffer.
        """
        self.buffer_idx = (self.buffer_idx + steps) % len(self.buffer)

    def decrement(self, steps: int = 1) -> None:
        """
        Moves index backward without changing the buffer.
        """
        self.buffer_idx = (self.buffer_idx - steps) % len(self.buffer)

    def put(self, frame: np.ndarray, gray: np.ndarray) -> None:
        """
        Pushes a frame and its grayscale version into the buffer.
        Then moves the index forward.
        """
        self.buffer[self.buffer_idx] = (frame, gray)
        self.increment()

    def get_forward(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns the content of the buffer at the current position.
        Then moves the index forward.
        """
        frame, gray = self.buffer[self.buffer_idx]
        self.increment()
        return frame, gray

    def get_back(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Moves the index backward.
        Then returns the content of the buffer at that index.
        """
        self.decrement()
        return self.buffer[self.buffer_idx]


def interpolate_polygons(
    cur_frame: np.ndarray,
    frame_buffer: FrameBuffer,
    num_frames: int,
    old_polygons: list[np.ndarray],
    cur_polygons: list[np.ndarray],
) -> list[tuple[np.ndarray, np.ndarray, list[np.ndarray]]]:
    """
    Approximates blurred polygons between keyframes.
    Returns a List of frames to write and their polygons.
    """
    # Propagate old polygons forward with optical flow
    frames_to_blur = []
    frame_buffer.decrement(num_frames + 1)
    _, prev_gray = frame_buffer.get_forward()
    prev_polygons = old_polygons
    for _ in range(num_frames):
        next_frame, next_gray = frame_buffer.get_forward()
        polygons = []
        for poly in prev_polygons:
            # TODO: user small replicated padding to increase stability on the edge
            # frame = cv2.copyMakeBorder(frame, padding, padding, padding, padding, cv2.BORDER_REPLICATE, None, 0)
            new_poly, _, _ = cv2.calcOpticalFlowPyrLK(
                prev_gray,
                next_gray,
                poly,
                None,
                winSize=(15, 15),
                maxLevel=10,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
            )
            avg_disp = np.sum(new_poly - poly, axis=0) / (poly.shape[0])
            polygons.append(poly + avg_disp)
        frames_to_blur.append((next_frame, next_gray, polygons))
        prev_gray = next_gray
        prev_polygons = polygons

    # Propagate new polygons backward with optical flow
    next_gray = cv2.cvtColor(cur_frame, cv2.COLOR_BGR2GRAY)
    frame_buffer.put(cur_frame, next_gray)
    next_polygons = cur_polygons
    for i in range(num_frames):
        _, prev_gray, inter_polygons = frames_to_blur[-i - 1]
        polygons = []
        for poly in next_polygons:
            # TODO: user small replicated padding to increase stability on the edge
            # frame = cv2.copyMakeBorder(frame, padding, padding, padding, padding, cv2.BORDER_REPLICATE, None, 0)
            new_poly, _, _ = cv2.calcOpticalFlowPyrLK(
                next_gray,
                prev_gray,
                poly,
                None,
                winSize=(15, 15),
                maxLevel=10,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
            )
            avg_disp = np.sum(new_poly - poly, axis=0) / (poly.shape[0])
            polygons.append(poly + avg_disp)
        inter_polygons.extend(polygons)
        next_gray = prev_gray
        next_polygons = polygons

    return frames_to_blur


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
    except Exception:
        # ffmpegcv cap.fps is not reliable
        fps_cap = cv2.VideoCapture(video_path)
        fps = fps_cap.get(cv2.CAP_PROP_FPS)
        fps_cap.release()

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
        try:
            blur_amount = int(os.environ.get("VIDEO_BLUR"))
            blur_amount = max(1, min(10, blur_amount))
        except Exception:
            blur_amount = 3
        blur_url = os.environ.get("BLUR_URL")

    frame_count = 0
    start = time.time()
    try:
        sample_rate = int(os.environ.get("SAMPLE"))
    except Exception:
        sample_rate = 1
    keyframe_count = 1 % sample_rate  # for sample_rate = 1
    old_polygons = []
    frame_buffer = FrameBuffer(sample_rate)
    prev_keyframe = 0
    while cap.isOpened():
        ret, cur_frame = cap.read()
        if ret:
            lgr.debug(f"Processing frame: {frame_count}")
            frame_count += 1

            if frames_enabled:
                save_frame(frame_count, cur_frame, frames_output_dir)

            if visualization_enabled:
                # adding filled rectangle on each frame
                visualized_frame = visualize_frame(
                    cur_frame, sdk_url, snapshot_api_token
                )
                out1.write(visualized_frame)

            if blur_enabled:
                if frame_count % sample_rate == keyframe_count:
                    cur_polygons, _ = get_blur_polygons(cur_frame, blur_url)

                    # Draw skip-frames
                    num_frames = frame_count - prev_keyframe - 1
                    frames_to_blur = interpolate_polygons(
                        cur_frame, frame_buffer, num_frames, old_polygons, cur_polygons
                    )
                    for frame, _, polygons in frames_to_blur:
                        blur_polygons(frame, polygons, blur_amount, out2)

                    # Draw current frame
                    blur_polygons(cur_frame, cur_polygons, blur_amount, out2)

                    # Update state variables
                    old_polygons = cur_polygons
                    prev_keyframe = frame_count
                else:
                    # Stack non-keyframes into buffer
                    gray = cv2.cvtColor(cur_frame, cv2.COLOR_BGR2GRAY)
                    frame_buffer.put(cur_frame, gray)
        else:
            break

    # Flush the frame buffer
    if blur_enabled and prev_keyframe != frame_count:
        cur_frame, _ = frame_buffer.get_back()
        cur_polygons, _ = get_blur_polygons(cur_frame, blur_url)

        # Draw skip-frames
        num_frames = frame_count - prev_keyframe - 1
        frames_to_blur = interpolate_polygons(
            cur_frame, frame_buffer, num_frames, old_polygons, cur_polygons
        )
        for frame, _, polygons in frames_to_blur:
            blur_polygons(frame, polygons, blur_amount, out2)

        # Draw current frame
        blur_polygons(cur_frame, cur_polygons, blur_amount, out2)

    lgr.debug(f"Frame count: {frame_count}")
    lgr.debug(f"Time taken: {time.time() - start}")

    cap.release()
    if out1:
        out1.release()
    if out2:
        out2.release()

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
        lgr.error(e)
        return jsonify({"error": str(e)}), 500

    return jsonify("Done."), 200


app.run(host="0.0.0.0", port=8081, debug=True)
