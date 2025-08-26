#!/usr/bin/env python

import argparse
import csv
import io
import json
import math
import sys
import time
from collections import OrderedDict
from itertools import combinations
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    from collections.abc import MutableMapping
else:
    # ruff: noqa
    from collections import MutableMapping  # type: ignore[attr-defined]


def parse_arguments(args_hook=lambda _: _):
    parser = argparse.ArgumentParser(
        description="Read license plates from images and output the result as JSON or CSV.",
        epilog="""Examples:
Process images from a folder:
  python plate_recognition.py -a MY_API_KEY /path/to/vehicle-*.jpg
Use the Snapshot SDK instead of the Cloud Api:
  python plate_recognition.py -s http://localhost:8080 /path/to/vehicle-*.jpg
Specify Camera ID and/or two Regions:
  plate_recognition.py -a MY_API_KEY --camera-id Camera1 -r us-ca -r th-37 /path/to/vehicle-*.jpg""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-a", "--api-key", help="Your API key.", required=False)
    parser.add_argument(
        "-r",
        "--regions",
        help="Match the license plate pattern of a specific region",
        required=False,
        action="append",
    )
    parser.add_argument(
        "-s",
        "--sdk-url",
        help="Url to self hosted sdk  For example, http://localhost:8080",
        required=False,
    )
    parser.add_argument(
        "--camera-id", help="Name of the source camera.", required=False
    )
    parser.add_argument("files", nargs="+", type=Path, help="Path to vehicle images")
    args_hook(parser)
    args = parser.parse_args()
    if not args.sdk_url and not args.api_key:
        raise Exception("api-key is required")
    return args


_session = None


def recognition_api(
    fp,
    regions=None,
    api_key=None,
    sdk_url=None,
    config=None,
    camera_id=None,
    timestamp=None,
    mmc=None,
    exit_on_error=True,
):
    if regions is None:
        regions = []
    if config is None:
        config = {}
    global _session
    data = dict(regions=regions, config=json.dumps(config))
    if camera_id:
        data["camera_id"] = camera_id
    if mmc:
        data["mmc"] = mmc
    if timestamp:
        data["timestamp"] = timestamp
    response = None
    if sdk_url:
        fp.seek(0)
        if "container-api" in sdk_url:
            response = requests.post(
                "https://container-api.parkpow.com/api/v1/predict/",
                files=dict(image=fp),
                headers={"Authorization": "Token " + api_key},
            )
        else:
            response = requests.post(
                sdk_url + "/v1/plate-reader/", files=dict(upload=fp), data=data
            )
    else:
        if not _session:
            _session = requests.Session()
            _session.headers.update({"Authorization": "Token " + api_key})
        for _ in range(3):
            fp.seek(0)
            response = _session.post(
                "https://api.platerecognizer.com/v1/plate-reader/",
                files=dict(upload=fp),
                data=data,
            )
            if response.status_code == 429:  # Max calls per second reached
                time.sleep(1)
            else:
                break

    if response is None:
        return {}
    if response.status_code < 200 or response.status_code > 300:
        print(response.text)
        if exit_on_error:
            exit(1)
    return response.json(object_pairs_hook=OrderedDict)


def flatten_dict(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            if isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
    return dict(items)


def flatten(result):
    plates = result["results"]
    del result["results"]
    if "usage" in result:
        del result["usage"]
    flattened_data = []  # Accumulate flattened data for each plate
    if not plates:
        data = result.copy()
        data.update(flatten_dict({}))  # Assuming flatten_dict can handle an empty dict
        flattened_data.append(data)
    else:
        for plate in plates:
            data = result.copy()
            data.update(flatten_dict(plate))
            flattened_data.append(data)
    return flattened_data


def save_cropped(api_res, path, args):
    dest = args.crop_lp or args.crop_vehicle
    dest.mkdir(exist_ok=True, parents=True)
    image = Image.open(path).convert("RGB")
    for i, result in enumerate(api_res.get("results", []), 1):
        if args.crop_lp and result["plate"]:
            box = result["box"]
            cropped = image.crop((box["xmin"], box["ymin"], box["xmax"], box["ymax"]))
            cropped.save(
                dest / f'{result["plate"]}_{result["region"]["code"]}_{path.name}'
            )
        if args.crop_vehicle and result["vehicle"]["score"]:
            box = result["vehicle"]["box"]
            cropped = image.crop((box["xmin"], box["ymin"], box["xmax"], box["ymax"]))
            make_model = result.get("model_make", [None])[0]
            filename = f'{i}_{result["vehicle"]["type"]}_{path.name}'
            if make_model:
                filename = f'{make_model["make"]}_{make_model["model"]}_' + filename
            cropped.save(dest / filename)


def is_detection_mode_vehicle(engine_config):
    if not engine_config:
        return False

    try:
        engine_config_dict = json.loads(engine_config)
    except (TypeError, json.JSONDecodeError):
        return False

    return engine_config_dict.get("detection_mode") == "vehicle"


def transform_result(input_data):
    output = OrderedDict(
        [
            ("filename", input_data.get("filename")),
            ("timestamp", input_data.get("timestamp")),
            ("camera_id", input_data.get("camera_id")),
            ("results", []),
        ]
    )

    no_plate_box = OrderedDict(
        [("xmin", None), ("ymin", None), ("xmax", None), ("ymax", None)]
    )
    no_plate_region = OrderedDict([("code", None), ("score", None)])

    for result in input_data.get("results", []):
        # Process plate data if available
        plate_data = result.get("plate")
        if plate_data:
            props = plate_data.get("props", {})
            plate_candidates = props.get("plate", [])
            top_plate = plate_candidates[0] if plate_candidates else None

            region_candidates = props.get("region", [])
            top_region = region_candidates[0] if region_candidates else None
            region_entry = (
                OrderedDict(
                    [
                        ("code", top_region.get("value")),
                        ("score", top_region.get("score")),
                    ]
                )
                if top_region
                else None
            )
        else:
            plate_candidates = []
            top_plate = None
            region_entry = None

        # Skip if vehicle data is missing
        vehicle_data = result.get("vehicle")
        if not vehicle_data:
            continue

        # Process vehicle properties
        v_props = vehicle_data.get("props", {})
        model_make = v_props.get("make_model", [])

        colors = [
            OrderedDict([("color", c.get("value")), ("score", c.get("score"))])
            for c in v_props.get("color", [])
        ]
        orientations = [
            OrderedDict([("orientation", o.get("value")), ("score", o.get("score"))])
            for o in v_props.get("orientation", [])
        ]

        candidates = [
            OrderedDict([("score", cand.get("score")), ("plate", cand.get("value"))])
            for cand in plate_candidates
        ]

        vehicle_entry = OrderedDict(
            [
                ("score", vehicle_data.get("score")),
                ("type", vehicle_data.get("type")),
                ("box", vehicle_data.get("box")),
            ]
        )

        transformed_result = OrderedDict(
            [
                ("box", plate_data.get("box") if plate_data else no_plate_box),
                ("plate", top_plate.get("value") if top_plate else None),
                ("region", region_entry if top_plate else no_plate_region),
                ("score", top_plate.get("score") if top_plate else None),
                ("candidates", candidates if plate_data else None),
                ("dscore", plate_data.get("score") if plate_data else None),
                ("vehicle", vehicle_entry),
                ("model_make", model_make),
                ("color", colors),
                ("orientation", orientations),
            ]
        )

        output["results"].append(transformed_result)

    output["usage"] = input_data.get("usage", {})
    output["processing_time"] = input_data.get("processing_time")
    return output


def save_results(results, args):
    path = args.output_file
    if not Path(path).parent.exists():
        print("%s does not exist" % path)
        return
    if not results:
        return
    if args.format == "json":
        with open(path, "w") as fp:
            json.dump(results, fp)
    elif args.format == "csv":
        fieldnames = []
        for result in results[:10]:
            data = (
                transform_result(result)
                if is_detection_mode_vehicle(args.engine_config)
                else result
            )
            candidates = flatten(data.copy())
            for candidate in candidates:
                if len(fieldnames) < len(candidate):
                    fieldnames = candidate.keys()
        with open(path, "w", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            for result in results:
                result_data = (
                    transform_result(result)
                    if is_detection_mode_vehicle(args.engine_config)
                    else result
                )
                flattened_results = flatten(result_data)
                for flattened_result in flattened_results:
                    writer.writerow(flattened_result)


def custom_args(parser):
    parser.epilog += """
Specify additional engine configuration:
  plate_recognition.py -a MY_API_KEY --engine-config \'{"region":"strict"}\' /path/to/vehicle-*.jpg
Specify an output file and format for the results:
  plate_recognition.py -a MY_API_KEY -o data.csv --format csv /path/to/vehicle-*.jpg
Enable Make Model and Color prediction:
  plate_recognition.py -a MY_API_KEY --mmc /path/to/vehicle-*.jpg"""

    parser.add_argument("--engine-config", help="Engine configuration.")
    parser.add_argument(
        "--crop-lp", type=Path, help="Save cropped license plates to folder."
    )
    parser.add_argument(
        "--crop-vehicle", type=Path, help="Save cropped vehicles to folder."
    )
    parser.add_argument("-o", "--output-file", type=Path, help="Save result to file.")
    parser.add_argument(
        "--format",
        help="Format of the result.",
        default="json",
        choices="json csv".split(),
    )
    parser.add_argument(
        "--mmc",
        action="store_true",
        help="Predict vehicle make and model. Only available to paying users.",
    )
    parser.add_argument(
        "--show-boxes",
        action="store_true",
        help="Draw bounding boxes around license plates and display the resulting image.",
    )
    parser.add_argument(
        "--annotate-images",
        action="store_true",
        help="Draw bounding boxes around license plates and save the resulting image.",
    )
    parser.add_argument(
        "--split-image",
        action="store_true",
        help="Do extra lookups on parts of the image. Useful on high resolution images.",
    )

    parser.add_argument("--split-x", type=int, default=0, help="Splits on the x-axis")

    parser.add_argument("--split-y", type=int, default=0, help="Splits on the y-axis")

    parser.add_argument(
        "--split-overlap",
        type=int,
        default=10,
        help="Percentage of window overlap when splitting",
    )


def draw_bb(im, data, new_size=(1920, 1050), text_func=None):
    draw = ImageDraw.Draw(im)
    font_path = Path("assets/DejaVuSansMono.ttf")
    if font_path.exists():
        font = ImageFont.truetype(str(font_path), 10)
    else:
        font = ImageFont.load_default()
    rect_color = (0, 255, 0)
    for result in data:
        b = result["box"]
        coord = [(b["xmin"], b["ymin"]), (b["xmax"], b["ymax"])]
        draw.rectangle(coord, outline=rect_color)
        draw.rectangle(
            ((coord[0][0] - 1, coord[0][1] - 1), (coord[1][0] - 1, coord[1][1] - 1)),
            outline=rect_color,
        )
        draw.rectangle(
            ((coord[0][0] - 2, coord[0][1] - 2), (coord[1][0] - 2, coord[1][1] - 2)),
            outline=rect_color,
        )
        if text_func:
            text = text_func(result)
            (text_width, text_height) = font.font.getsize(text)[0]
            margin = math.ceil(0.05 * text_height)
            draw.rectangle(
                [
                    (b["xmin"] - margin, b["ymin"] - text_height - 2 * margin),
                    (b["xmin"] + text_width + 2 * margin, b["ymin"]),
                ],
                fill="white",
            )
            draw.text(
                (b["xmin"] + margin, b["ymin"] - text_height - margin),
                text,
                fill="black",
                font=font,
            )

    if new_size:
        im = im.resize(new_size)
    return im


def text_function(result):
    return result["plate"]


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


def clean_objs(objects, threshold=0.1):
    # Only keep the ones with best score or no overlap
    for o1, o2 in combinations(objects, 2):
        if (
            "remove" in o1
            or "remove" in o2
            or bb_iou(o1["box"], o2["box"]) <= threshold
        ):
            continue
        if o1["score"] > o2["score"]:
            o2["remove"] = True
        else:
            o1["remove"] = True
    return [x for x in objects if "remove" not in x]


def merge_results(images):
    result = dict(results=[])
    for data in images:
        for item in data["prediction"]["results"]:
            result["results"].append(item)
            for b in [item["box"], item["vehicle"].get("box", {})]:
                b["ymin"] += data["y"]
                b["xmin"] += data["x"]
                b["ymax"] += data["y"]
                b["xmax"] += data["x"]
    result["results"] = clean_objs(result["results"])
    return result


def inside(a, b):
    return (
        a["xmin"] > b["xmin"]
        and a["ymin"] > b["ymin"]
        and a["xmax"] < b["xmax"]
        and a["ymax"] < b["ymax"]
    )


def post_processing(results):
    new_list = []
    for item in results["results"]:
        if item["score"] < 0.2 and any(
            [inside(x["box"], item["box"]) for x in results["results"] if x != item]
        ):
            continue
        new_list.append(item)
    results["results"] = new_list
    return results


def output_image(args, path, results):
    if args.show_boxes or args.annotate_images and "results" in results:
        image = Image.open(path)
        annotated_image = draw_bb(image, results["results"], None, text_function)
        if args.show_boxes:
            annotated_image.show()
        if args.annotate_images:
            annotated_image.save(path.with_name(f"{path.stem}_annotated{path.suffix}"))
    if args.crop_lp or args.crop_vehicle:
        save_cropped(results, path, args)


def process_split_image(path, args, engine_config):
    if args.split_x == 0 or args.split_y == 0:
        raise ValueError("Please specify --split-x or --split-y")

    # Predictions
    fp = Image.open(path)
    if fp.mode != "RGB":
        fp = fp.convert("RGB")
    images = [((0, 0), fp)]  # Entire image

    overlap_pct = args.split_overlap

    window_width = fp.width / (args.split_x + 1)
    window_height = fp.height / (args.split_y + 1)

    overlap_width = int(window_width * overlap_pct / 100)
    overlap_height = int(window_height * overlap_pct / 100)

    draw = ImageDraw.Draw(fp)

    for i in range(args.split_x + 1):
        for j in range(args.split_y + 1):
            ymin = j * window_height
            ymax = ymin + window_height

            xmin = i * window_width
            xmax = xmin + window_width

            # Add x-axis Overlap
            if i == 0:  # Overlap `end` of first Window only
                xmax = xmax + overlap_width
            elif i == args.split_x:  # Overlap `start` of last Window only
                xmin = xmin - overlap_width
            else:  # Overlap both `start` and `end` of middle Windows
                xmin = xmin - overlap_width
                xmax = xmax + overlap_width

            # Add y-axis Overlap
            if j == 0:  # Overlap `bottom` of first Window only
                ymax = ymax + overlap_height
                pass
            elif j == args.split_y:  # Overlap `top` of last Window only
                ymin = ymin - overlap_height
                pass
            else:  # Overlap both `top` and `bottom` of middle Windows
                ymin = ymin - overlap_height
                ymax = ymax + overlap_height

            images.append(((xmin, ymin), fp.crop((xmin, ymin, xmax, ymax))))

    # Inference
    api_results = {}
    results = []
    usage = []
    camera_ids = []
    timestamps = []
    processing_times = []
    for (x, y), im in images:
        im_bytes = io.BytesIO()
        im.save(im_bytes, "JPEG", quality=95)
        im_bytes.seek(0)
        api_res = recognition_api(
            im_bytes,
            args.regions,
            args.api_key,
            args.sdk_url,
            config=engine_config,
            camera_id=args.camera_id,
            mmc=args.mmc,
        )
        results.append(dict(prediction=api_res, x=x, y=y))
        if "usage" in api_res:
            usage.append(api_res["usage"])
        camera_ids.append(api_res["camera_id"])
        timestamps.append(api_res["timestamp"])
        processing_times.append(api_res["processing_time"])

    api_results["filename"] = Path(path).name
    api_results["timestamp"] = timestamps[len(timestamps) - 1]
    api_results["camera_id"] = camera_ids[len(camera_ids) - 1]
    results = post_processing(merge_results(results))
    results = OrderedDict(list(api_results.items()) + list(results.items()))
    if len(usage):
        results["usage"] = usage[len(usage) - 1]
    results["processing_time"] = round(sum(processing_times), 3)

    # Set bounding box padding
    for item in results["results"]:
        # Decrease padding size for large bounding boxes
        b = item["box"]
        width, height = b["xmax"] - b["xmin"], b["ymax"] - b["ymin"]
        padding_x = int(max(0, width * (0.3 * math.exp(-10 * width / fp.width))))
        padding_y = int(max(0, height * (0.3 * math.exp(-10 * height / fp.height))))
        b["xmin"] = b["xmin"] - padding_x
        b["ymin"] = b["ymin"] - padding_y
        b["xmax"] = b["xmax"] + padding_x
        b["ymax"] = b["ymax"] + padding_y

    output_image(args, path, results)
    return results


def process_full_image(path, args, engine_config):
    with open(path, "rb") as fp:
        api_res = recognition_api(
            fp,
            args.regions,
            args.api_key,
            args.sdk_url,
            config=engine_config,
            camera_id=args.camera_id,
            mmc=args.mmc,
        )

    output_image(args, path, api_res)
    return api_res


def main():
    args = parse_arguments(custom_args)
    paths = args.files

    results = []
    engine_config = {}
    if args.engine_config:
        try:
            engine_config = json.loads(args.engine_config)
        except json.JSONDecodeError as e:
            print(e)
            return
    for path in paths:
        if not path.exists():
            continue
        if Path(path).is_file():
            if args.split_image:
                results.append(process_split_image(path, args, engine_config))
            else:
                results.append(process_full_image(path, args, engine_config))
    if args.output_file:
        save_results(results, args)
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
