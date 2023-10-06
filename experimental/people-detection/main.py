import argparse
import datetime
import logging
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from models.experimental import Ensemble
from utils.datasets import letterbox
from utils.general import non_max_suppression, scale_coords
from utils.plots import plot_one_box
from utils.torch_utils import select_device, time_synchronized
from webhook import WebhookSender

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger("main")

LOG_DEBUG = "DEBUG"


def send_webhook(url, cv2_image, data):
    lgr.debug(f"Data: {data}")
    try:
        sender = WebhookSender(url)
        sender.execute(cv2_image, data)
    except Exception as e:
        lgr.error("An error occurred:", exc_info=e)
        exit(1)


def run_prediction(img0, device, half, model, args):
    # Get names and colors
    names = model.module.names if hasattr(model, "module") else model.names
    # Padded resize
    img_size = 640
    stride = 32
    img = letterbox(img0, img_size, stride=stride)[0]
    # Convert
    img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
    img = np.ascontiguousarray(img)
    img = torch.from_numpy(img).to(device)
    img = img.half() if half else img.float()  # uint8 to fp16/32
    img /= 255.0  # 0 - 255 to 0.0 - 1.0
    if img.ndimension() == 3:
        img = img.unsqueeze(0)

    # Apply NMS
    conf_threshold = 0.7  # object confidence threshold
    iou_threshold = 0.45  # IOU threshold for NMS
    classes = None
    agnostic_nms = False

    # Inference
    t1 = time_synchronized()
    pred = model(img, augment=False)[0]
    pred = non_max_suppression(
        pred, conf_threshold, iou_threshold, classes=classes, agnostic=agnostic_nms
    )
    t2 = time_synchronized()
    processing_time = t2 - t1

    # Print time (inference + NMS)
    lgr.debug(f"Inference Time: ({processing_time:.3f}s)")

    # Generate timestamp for
    dt = datetime.datetime.utcfromtimestamp(t1)
    timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Process detections
    results = []

    for det in pred:
        # Rescale boxes from img_size to im0 size
        det[:, :4] = scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
        # Write results
        for *xyxy, conf, cls in reversed(det.tolist()):
            cls = int(cls)
            # cls 1 -  head
            # cls 0 -  person
            # Skip heads if disabled
            if cls == 1 and not args.heads:
                continue

            # Add bbox to images if DEBUG log level
            if LOG_LEVEL == LOG_DEBUG:
                plot_one_box(xyxy, img0)

            results.append({"class": names[cls], "xy_xy": xyxy, "confidence": conf})

    if len(results) > 0:
        data = {
            "results": results,
            "processing_time": processing_time,
            "timestamp": timestamp,
        }
        send_webhook(args.webhook, img0 if args.image else None, data)

    # If DEBUG, exit after sending 1 webhook with detections
    # if LOG_LEVEL == LOG_DEBUG and len(results) > 0:
    #     exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Detect persons in live camera feed or video file"
    )
    parser.add_argument(
        "-url",
        required=True,
        type=str,
        help="Video URL, rtsp://, rtmp://, http:// or File path in a mounted volume",
    )
    parser.add_argument(
        "-device",
        default="",
        help="Use GPU or CPU, cpu or a cuda device i.e. 0 or 0,1,2,3",
    )
    parser.add_argument("-webhook", required=True, type=str, help="Webhook Target URL")
    parser.add_argument(
        "-image",
        action="store_true",
        default=False,
        help="Include image in webhook payload",
    )
    parser.add_argument(
        "-heads",
        action="store_true",
        default=False,
        help="Detect heads and include in results",
    )
    parser.add_argument(
        "-weights", type=Path, default="crowdhuman_yolov5m.pt", help="Model Weights"
    )
    parser.add_argument("-sample", type=int, default=2, help="Sample Rate")
    args = parser.parse_args()

    device = select_device(args.device)
    half = device.type != "cpu"  # half precision only supported on CUDA

    md = Ensemble()
    md.append(
        torch.load(args.weights, map_location=device)["model"].float().fuse().eval()
    )
    model = md[-1]

    for m in model.modules():
        if isinstance(m, nn.Upsample):
            m.recompute_scale_factor = None

    if half:
        model.half()  # to FP16

    cap = cv2.VideoCapture(args.url)
    if not cap.isOpened():
        lgr.error(f"Error loading video: {args.url}")
        exit(1)

    frame_number = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frame_number += 1
            # Process every nth frame
            if frame_number % args.sample == 0:
                run_prediction(frame, device, half, model, args)
            # Reset frame number
            if frame_number > 10000:
                frame_number = 0
        else:
            break
    cap.release()


if __name__ == "__main__":
    main()
