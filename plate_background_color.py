import io
import csv
import sys
import json
import argparse
import logging
import base64
import requests
import numpy as np

from pathlib import Path
from PIL import Image, UnidentifiedImageError

# Compatibility import for MutableMapping based on Python version
if sys.version_info.major == 3 and sys.version_info.minor >= 10:
    from collections.abc import MutableMapping
else:
    # ruff: noqa
    from collections import MutableMapping  # type: ignore[attr-defined]

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def flatten_dict(d, parent_key="", sep="_"):
    """Flatten a nested dictionary into a single-level dictionary with concatenated keys."""
    items = []
    for k, v in d.items():
        if k == "result":
            # Flatten the result dictionary without adding the prefix
            items.extend(flatten_dict(v, parent_key, sep=sep).items())
        else:
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, MutableMapping):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, json.dumps(v) if isinstance(v, list) else v))
    return dict(items)


def flatten(plates_data):
    """Flatten the plates data structure by removing unwanted fields."""
    plates = plates_data["plates"]
    flattened_data = []
    for plate in plates:
        if "polygon" in plate:
            del plate["polygon"]  # Remove polygon data
        data = flatten_dict(plate)
        flattened_data.append(data)
    return flattened_data


def post_image_for_blur(img_path, args):
    """Send image data to the blur API and return the polygon response."""
    sdk_url = args.sdk_url
    api_key = args.api_key
    try:
        img_byte_arr = io.BytesIO()
        img_path.save(img_byte_arr, "JPEG", quality=95)
        img_bytes = img_byte_arr.getvalue()

        files = {"upload": img_bytes}
        data = {"config": '{"mode":"normal","threshold_d":0.2, "threshold_o":0.6}'}

        if sdk_url:
            response = requests.post(sdk_url, files=files, data=data)
        else:
            response = requests.post(
                "https://blur.platerecognizer.com/v1/blur",
                files=files,
                data=data,
                headers={"Authorization": f"Token {api_key}"},
            )

        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"API request error: {e}")
        return None


def get_aspect_ratio(polygon):
    # Calculate the aspect ratio of a polygon defined by its vertices
    distances = []
    num_points = len(polygon)

    for i in range(num_points):
        for j in range(i + 1, num_points):
            distance = np.linalg.norm(np.array(polygon[i]) - np.array(polygon[j]))
            distances.append(distance)

    # Ensure there are enough unique distances for calculations
    unique_widths = sorted(set(distances), reverse=True)
    longest_distance = unique_widths[2] if len(unique_widths) > 2 else 0

    unique_distances = sorted(set(distances))
    shortest_distance = unique_distances[1] if len(unique_distances) > 1 else 0

    # Find the points for the shortest distance
    second_shortest_points = (None, None)
    for i in range(num_points):
        for j in range(i + 1, num_points):
            distance = np.linalg.norm(np.array(polygon[i]) - np.array(polygon[j]))
            if distance == shortest_distance:
                second_shortest_points = (polygon[i], polygon[j])
                break
        if second_shortest_points[0] is not None:
            break

    # Find the points for the longest distance
    longest_width_points = (None, None)
    for i in range(num_points):
        for j in range(i + 1, num_points):
            distance = np.linalg.norm(np.array(polygon[i]) - np.array(polygon[j]))
            if distance == longest_distance:
                longest_width_points = (polygon[i], polygon[j])
                break
        if longest_width_points[0] is not None:
            break

    return longest_distance / shortest_distance if shortest_distance != 0 else 0


def predict_color(cropped_image):
    """Process a cropped image by sending it for prediction."""
    cropped_image_bytes = io.BytesIO()
    cropped_image.save(cropped_image_bytes, "JPEG", quality=95)
    cropped_image_bytes.seek(0)
    b64_data = base64.b64encode(cropped_image_bytes.read()).decode("utf-8")

    predict_request = '{"instances" : [{"b64": "%s"}]}' % b64_data
    try:
        response = requests.post(
            "http://localhost:8501/v1/models/classifier:predict", data=predict_request
        )
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"API request error: {e}")
        return None


def crop_box(box, direction, crop_percent):
    """Crop the box coordinates by a certain percentage from a specified direction."""
    height = box["ymax"] - box["ymin"]
    width = box["xmax"] - box["xmin"]

    # Calculate crop amount based on direction
    crop_amount = (
        (height - (height * crop_percent))
        if direction == "top"
        else width * crop_percent
    )

    if direction == "top":
        new_ymin = box["ymin"]
        new_ymax = box["ymax"] - crop_amount
        new_xmin = box["xmin"]
        new_xmax = box["xmax"]
    elif direction == "left":
        new_xmin = box["xmin"]
        new_xmax = box["xmin"] + crop_amount
        new_ymin = box["ymin"]
        new_ymax = box["ymax"]
    else:
        raise ValueError("Invalid direction. Please choose from 'top' or 'left'")

    return {"xmin": new_xmin, "xmax": new_xmax, "ymin": new_ymin, "ymax": new_ymax}


def reorder_plate_data(filename, data, predictions):
    """Reorder the plate data structure and insert the predictions."""
    prediction = predictions["predictions"][0]
    colors = prediction["color"]
    scores = prediction["score"]

    highest_color_score = max(scores)
    highest_color_index = scores.index(highest_color_score)
    plate_color = colors[highest_color_index]

    for plate_data in data["plates"]:
        new_result = {
            "filename": filename,
            "box": plate_data["result"]["box"],
            "plate": plate_data["result"]["plate"],
            "plate_color": plate_color,
            "region": plate_data["result"]["region"],
            "score": plate_data["result"]["score"],
            "plate_color_score": highest_color_score,
            "predictions": predictions["predictions"],
            "candidates": plate_data["result"]["candidates"],
            "dscore": plate_data["result"]["dscore"],
            "vehicle": {
                "score": plate_data["result"]["vehicle"]["score"],
                "type": plate_data["result"]["vehicle"]["type"],
                "box": plate_data["result"]["vehicle"]["box"],
            },
        }
        plate_data["result"] = new_result

    return data


def process_image(image_path, args):
    """Process a single image for license plate detection and prediction."""
    try:
        with Image.open(image_path) as img:
            crop_percentage = args.crop_percentage
            response = post_image_for_blur(img, args)

            for plate in response["plates"]:
                aspect_ratio = get_aspect_ratio(plate.get("polygon"))
                plate_box = plate.get("result")["box"]

                # Determine crop direction based on aspect ratio
                crop_direction = "left" if aspect_ratio > 2.379 else "top"
                crop_bounding_box = crop_box(plate_box, crop_direction, crop_percentage)

                # Crop the image based on the new bounding box
                cropped_img = img.crop(
                    (
                        crop_bounding_box["xmin"],
                        crop_bounding_box["ymin"],
                        crop_bounding_box["xmax"],
                        crop_bounding_box["ymax"],
                    )
                )

                predictions = predict_color(cropped_img)
                logger.info(
                    f"License plate background color processed: {image_path.name}"
                )
                return reorder_plate_data(image_path.name, response, predictions)

    except UnidentifiedImageError:
        logger.error(f"Cannot identify image file {image_path}")
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")


def save_results(results, args):
    """Save the processed results to a CSV file."""
    path = args.output_file
    if not Path(path).parent.exists():
        logger.error(f"{path} does not exist")
        return
    if not results:
        return

    fieldnames = []
    # Determine fieldnames based on results
    for result in results[:10]:
        candidates = flatten(result.copy())
        for candidate in candidates:
            if len(fieldnames) < len(candidate):
                fieldnames = candidate.keys()
    with open(path, "w") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            flattened_results = flatten(result)
            for flattened_result in flattened_results:
                writer.writerow(flattened_result)


def validate_crop_percentage(value):
    """Validate the crop percentage argument."""
    try:
        f = float(value)
        if 0.0 < f <= 1.0:
            return f
        else:
            raise argparse.ArgumentTypeError(
                "Crop percentage must be between 0.0 and 1.0."
            )
    except ValueError:
        raise argparse.ArgumentTypeError("Crop percentage must be a float.")


def parse_arguments():
    """Parse command-line arguments for the script."""
    parser = argparse.ArgumentParser(
        description="This script uses the Blur to crop it to the aspect ratio of a license plate and running it with License Plate Background Color"
    )
    parser.add_argument("--api-key", help="Your Blur API key.", required=False)
    parser.add_argument("--sdk-url", type=str, help="The URL of Blur SDK")
    parser.add_argument(
        "--images",
        type=Path,
        required=True,
        help="The directory for the image/s to be processed",
    )
    parser.add_argument(
        "--crop-percentage",
        type=validate_crop_percentage,
        required=True,
        help="The percentage of the image to crop (0.0 to 1.0)",
    )
    parser.add_argument(
        "--output-file", type=Path, required=True, help="Save result to file."
    )

    args = parser.parse_args()
    if not args.sdk_url and not args.api_key:
        raise Exception("Either sdk_url or api_key is required")
    return args


def main():
    """Main function to run the image processing script."""
    args = parse_arguments()
    images = args.images
    results = []

    # Validate image directory
    image_files = Path(images)
    if not image_files.exists() or not image_files.is_dir():
        logger.error(f"Invalid image directory: {images}")
        return

    # Process each image in the directory
    for image_path in image_files.glob("*"):
        if not image_path.is_file():
            logger.warning(f"Skipping non-file {image_path}")
            continue

        results.append(process_image(image_path, args))

    save_results(results, args)


if __name__ == "__main__":
    main()