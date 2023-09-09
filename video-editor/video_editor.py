import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from queue import Queue

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
BASE_WORKING_DIR = "/home/incrediblame/Downloads/"


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


def blur_frame(cv2_frame, blur_url):
    blur_response = blur_api(cv2_frame, blur_url)
    polygons = [np.array(plate['polygon'], dtype=np.int32) for plate in blur_response.json()['plates']]
    # arr = np.asarray(bytearray(blur_response.content), dtype=np.uint8)
    # blurred_frame = cv2.imdecode(arr, -1)  # 'Load it as it is'

    # Convert to int coordinates

    # Blur polygons
    blurred_frame = cv2_frame.copy()
    centers = np.empty((len(polygons), 2), dtype=np.float32)
    for i, poly in enumerate(polygons):
        centers[i] = np.mean(poly, axis=0)
        cv2.fillPoly(blurred_frame, [poly], (0, 0, 255))

    return blurred_frame, polygons, centers


def match_polygons(old_centers, new_centers):
    print(f"Old centers: {old_centers}")
    print(f"New centers: {new_centers}")
    DIST_THRESHOLD = 50
    matches = []
    num_new_centers = new_centers.shape[0]
    if num_new_centers > 0:
        new_indices = set(range(num_new_centers))
        for i, old_point in enumerate(old_centers):
            # if old_centers.shape[0] == 1 and new_centers.shape[0] == 2:
            #     print(np.linalg.norm(new_centers - old_point, axis=1))
            best_idx = np.argmin(np.linalg.norm(new_centers - old_point, axis=1))
            best_dist = np.linalg.norm(new_centers[best_idx] - old_point)
            if best_dist < DIST_THRESHOLD and best_idx in new_indices:
                matches.append((i, best_idx))
                new_indices.remove(best_idx)
            else:
                matches.append((i, -1))
        
        for i in new_indices:
            matches.append((-1, i))
    else:
        for i in range(old_centers.shape[0]):
            matches.append((i, -1))
    
    return matches


def interpolate(old_polygons, new_polygons, old_centers, new_centers, matches, fraction):
    inter_polygons = []
    for old_idx, new_idx in matches:
        if old_idx >= 0:
            old_point = old_centers[old_idx]
            old_poly = old_polygons[old_idx]
        else:
            old_point = new_centers[new_idx]
            old_poly = new_polygons[new_idx]
        if new_idx >= 0:
            new_point = new_centers[new_idx]
        else:
            new_point = old_centers[old_idx]
        
        disp = (new_point - old_point) * fraction
        # print(f"Fraction {fraction}, disp vector: {disp}")
        inter_poly = old_poly + disp
        inter_polygons.append(inter_poly.astype(np.int32))
    
    return inter_polygons


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

    fps_override = 5
    if visualization_enabled:
        output1_filename = (
            f"{BASE_WORKING_DIR}{filename_stem}_visualization.{video_format_ext}"
        )
        # out1 = init_writer(output1_filename, cap.fps)
        out1 = init_writer(output1_filename, fps_override)

    if blur_enabled:
        output2_filename = f"{BASE_WORKING_DIR}{filename_stem}_blur.{video_format_ext}"
        # out2 = init_writer(output2_filename, cap.fps)
        out2 = init_writer(output2_filename, fps_override)

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

    frame_count = 0
    start = time.time()
    sample_rate = 10
    old_polygons = []
    old_centers = np.array([])
    frame_buffer = Queue(maxsize=sample_rate)
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
                if frame_count % sample_rate == 1:
                    # Blurring each frame
                    blurred_frame, new_polygons, new_centers = blur_frame(frame, blur_url)
                    print("Old polygons")
                    for i, poly in enumerate(old_polygons):
                        print(f"{i}: {poly}")
                    print("New polygons")
                    for i, poly in enumerate(new_polygons):
                        print(f"{i}: {poly}")
                    matches = match_polygons(old_centers, new_centers)
                    time_delta = 0
                    print(f"Matches: {matches}")
                    while not frame_buffer.empty():
                        time_delta += 1
                        prev_frame = frame_buffer.get()
                        inter_polygons = interpolate(old_polygons, new_polygons, 
                                                     old_centers, new_centers, 
                                                     matches, time_delta / sample_rate)
                        print(f"Interpolated polygons: {inter_polygons}")
                        for poly in inter_polygons:
                            cv2.fillPoly(prev_frame, [poly], (0, 0, 255))
                        out2.write(prev_frame)
                    out2.write(blurred_frame)
                    old_polygons = new_polygons
                    old_centers = new_centers
                else:
                    frame_buffer.put(frame)
                
 
        else:
            break

    # Flush the frame buffer
    while not frame_buffer.empty():
        prev_frame = frame_buffer.get()
        for poly in old_polygons:
            cv2.fillPoly(prev_frame, [poly], (0, 0, 255))
        out2.write(prev_frame)
    
    cap.release()
    if out1:
        out1.release()
    if out2:
        out2.release()
    
    print(f"Time taken: {time.time() - start}")
    print(f"Frame count: {frame_count}")

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
