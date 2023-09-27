import argparse
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
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
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
        print(f"path1: {path1}")
        print(f"path2: {path2}")
        path3 = Path(path1) / Path(*path2.parts[2:])
    else:
        real_path = os.path.relpath(path2, common_prefix)
        print(f"common_prefix: {common_prefix}")
        print(f"real_path: {real_path}")
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


def process(
    args,
    path: Path,
    # data: dict,
    # face_detection_threshold: float,
    # exclusion,
    output: Path,
    # slices_count: int,
    # overlap: int,
):
    """
    Process An Image

    """
    # TODO blur_amount = int(os.getenv('BLUR', 3))
    lgr.debug(f"output path: {output}")

    # Read Image File
    with open(path, "rb") as fp:
        response = requests.post(args.blur_url, files=dict(upload=fp), stream=True)
        if response.status_code < 200 or response.status_code > 300:
            logging.error(response.text)
            raise Exception("Error performing blur")

        # TODO if json log. if file save
        # print(response.text)
        response_content_type = response.headers["Content-Type"]
        lgr.debug(f"response_content_type: {response_content_type}")
        if response_content_type == "application/json":
            # Print the JSON response.
            print(response.json())
        elif response_content_type.startswith("image/"):
            # Save the image file.
            with open(output, "wb") as f:
                f.write(response.content)
        else:
            # Print the raw response.
            raise Exception(
                f"Unexpected Response Content Type: {response_content_type}"
            )


def process_dir(
    input_dir: Path,
    args,
    # data: dict,
    # face_detection_threshold: float,
    # exclusion: Exclusion,
    output_dir: Path,
    rename_file,
    # slices_count,
    # overlap,
    resume,
):
    """
    Recursively Process Images in a directory

    :return:
    """
    for path in input_dir.iterdir():
        if path.is_dir():
            process_dir(
                path,
                args,
                # data,
                # face_detection_threshold,
                # exclusion,
                output_dir,
                rename_file,
                # slices_count,
                # overlap,
                resume,
            )
        elif path.name.startswith("blur-") or path.name.endswith(
            f"_clean{path.suffix}"
        ):
            lgr.debug(f"Skipping output file: {path}")
            continue
        else:
            lgr.info(f"Processing file: {path}")
            output_path = get_output_path(output_dir, path, rename_file)
            if resume and output_path.is_file():
                continue

            process(
                args,
                path,
                # data,
                # face_detection_threshold,
                # exclusion,
                output_path,
                # slices_count,
                # overlap,
            )


def main():
    parser = argparse.ArgumentParser(
        description="Blur plates and faces in a folder recursively"
    )
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=False)
    parser.add_argument("--camera_id", required=False)
    parser.add_argument("--config", required=False)
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
        help="Process the image in multiple horizontal chunks instead of a single one. Slower but more accurate.",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        required=False,
        default=20,
        help="Percentage of overlap when creating the chunks.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip blurred images. Checks if output path exists.",
        default=False,
    )
    parser.add_argument(
        "-b",
        "--blur-url",
        help="Url to blur sdk  For example, http://localhost:5000",
        required=True,
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
    process_dir(
        args.images,
        args,
        # face_detection_t,
        # exclusion,
        output_dir,
        rename_file,
        # slices_count,
        # args.overlap,
        args.resume,
    )
    end = time.time()
    tt = end - start
    lgr.debug(f"Processing complete. Time taken: {tt}")


if __name__ == "__main__":
    main()
