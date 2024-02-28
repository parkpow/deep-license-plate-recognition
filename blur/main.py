import argparse
import base64
import logging
import os
import sys
import time
from pathlib import Path

import requests

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(levelname)-5s  [%(name)s.%(lineno)d] => %(message)s",
)

lgr = logging.getLogger("blur")


def merge_paths(path1: Path, path2: Path):
    """
    This is path computation, No filesystem access

    path1 = Path('/images/')
    path2 = Path('/images/dir1/dir2/file4.jpg')
    print(merge_paths(path1, path2))
    # Output: /images/dir1/dir2/file4.jpg

    path1 = Path('/tmp/output/test_skip_resume3-output/')
    path2 = Path('/tmp/output/test_skip_resume3/dir1/dir2/file4.jpg')
    print(merge_paths(path1, path2))
    # Output: /tmp/output/test_skip_resume3-output/test_skip_resume3/dir1/dir2/file4.jpg

    path1 = Path('/output/test_skip_resume3-output/')
    path2 = Path('/images/test_skip_resume3/dir1/dir2/file4.jpg')
    print(merge_paths(path1, path2))
    # Output: /output/test_skip_resume3-output/test_skip_resume3/dir1/dir2/file4.jpg

    :param path1: dir
    :param path2: file
    :return:
    """
    common_prefix = os.path.commonpath([path1, path2])
    if common_prefix == "/":
        # Custom output dir, exclude the first (/images/) prefix
        lgr.debug(f"path1: {path1}")
        lgr.debug(f"path2: {path2}")
        path3 = Path(path1) / Path(*path2.parts[2:])
    else:
        real_path = os.path.relpath(path2, common_prefix)
        lgr.debug(f"common_prefix: {common_prefix}")
        lgr.debug(f"real_path: {real_path}")
        path3 = path1 / Path(real_path)

    return path3


def get_output_path(output_dir, path, rename_file):
    lgr.debug(f"get_output_path({output_dir}, {path}, {rename_file})")
    if rename_file:
        output = path.with_name(f"blur-{path.name}")
    else:
        output = merge_paths(output_dir, path)

    lgr.debug(f"Output: {output}")
    # Create output dirs if not exist
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def process(args, path: Path, output: Path, logo=None):
    """
    Process An Image
    """
    lgr.debug(f"output path: {output}")
    with open(path, "rb") as fp:
        data = {
            "camera_id": args.camera_id,
            "config": args.config,
            "et": args.et,
            "el": args.el,
            "eb": args.eb,
            "er": args.er,
            "xmin": args.xmin,
            "ymin": args.ymin,
            "xmax": args.xmax,
            "ymax": args.ymax,
            "split": args.split,
            "overlap": args.overlap,
            "faces": args.faces,
            "plates": args.plates,
        }
        if args.api_key:
            headers = {
                "Authorization": f"Token {args.api_key}",
            }
        else:
            headers = None

        response = requests.post(
            args.blur_url,
            headers=headers,
            files={"logo": logo, "upload": fp},
            data=data,
            stream=True,
        )
        lgr.debug(f"Response: {response}")
        if response.status_code < 200 or response.status_code > 300:
            logging.error(response.text)
            raise Exception(f"Error performing blur: {response.text}")

        blur_data = response.json().get("blur")
        if blur_data is None:
            raise Exception(
                "Error - ensure blurring on server is enabled - "
                "https://guides.platerecognizer.com/docs/blur/api-reference#post-parameters"
            )
        else:
            base64_encoded_data = blur_data["base64"]
            decoded_bytes = base64.b64decode(base64_encoded_data)
            with open(output, "wb") as f:
                f.write(decoded_bytes)


def process_dir(input_dir: Path, args, output_dir: Path, rename_file, resume):
    """
    Recursively Process Images in a directory

    :return:
    """
    logo_bytes = None
    if args.logo:
        with open(args.logo, "rb") as fp:
            logo_bytes = fp.read()

    for path in input_dir.glob("**/*"):
        if path.is_file() and not path.name.startswith("blur-"):
            lgr.info(f"Processing file: {path}")
            output_path = get_output_path(output_dir, path, rename_file)
            if resume and output_path.is_file():
                continue
            process(args, path, output_path, logo_bytes)


def main():
    parser = argparse.ArgumentParser(
        description="Blur plates and faces in a folder recursively"
    )
    parser.add_argument("-a", "--api-key", help="Your API key.", required=False)
    parser.add_argument(
        "-b",
        "--blur-url",
        help="Url to blur SDK. Example http://localhost:5000",
        required=True,
    )
    parser.add_argument(
        "--images",
        type=Path,
        required=True,
        help="Folder containing images to process.",
    )
    parser.add_argument(
        "--logo",
        type=Path,
        required=False,
        help="Logo file path.",
    )
    parser.add_argument(
        "--plates", type=int, default="10", help="Plate blur intensity."
    )
    parser.add_argument("--faces", type=int, default="10", help="Face blur intensity.")
    parser.add_argument(
        "--camera_id", required=False, help="Camera ID forward to Snapshot"
    )
    parser.add_argument(
        "--config", required=False, help="Extra engine config forward to Snapshot"
    )
    parser.add_argument(
        "--et", type=float, required=False, default=0.0, help="Exclusion margin top."
    )
    parser.add_argument(
        "--el", type=float, required=False, default=0.0, help="Exclusion margin left."
    )
    parser.add_argument(
        "--eb", type=float, required=False, default=0.0, help="Exclusion margin bottom."
    )
    parser.add_argument(
        "--er", type=float, required=False, default=0.0, help="Exclusion margin right."
    )
    parser.add_argument(
        "--xmin", type=int, required=False, help="Exclusion xmin.", nargs="*"
    )
    parser.add_argument(
        "--ymin", type=int, required=False, help="Exclusion ymin.", nargs="*"
    )
    parser.add_argument(
        "--xmax", type=int, required=False, help="Exclusion xmax.", nargs="*"
    )
    parser.add_argument(
        "--ymax", type=int, required=False, help="Exclusion ymax.", nargs="*"
    )
    parser.add_argument(
        "--split",
        type=int,
        required=False,
        help="Split large images into horizontal chunks to increase predictions.",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        required=False,
        help="Percentage of overlap when splitting.",
    )
    parser.add_argument("--output", type=Path, required=False, help="Output directory.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip already blurred images.",
        default=False,
    )
    args = parser.parse_args()

    if args.output is not None:
        if args.output.is_dir():
            output_dir = args.output
            if output_dir == args.images:
                lgr.info(
                    "--output ignored, Files are renamed when outputting to same directory."
                )
            rename_file = False
        else:
            sys.exit(
                f"Output directory is missing or invalid. Ensure path exists: {args.output}"
            )
    else:
        output_dir = args.images
        rename_file = True

    start = time.time()
    process_dir(args.images, args, output_dir, rename_file, args.resume)
    end = time.time()
    tt = end - start
    lgr.debug(f"Processing complete. Time taken: {tt}")


if __name__ == "__main__":
    main()
