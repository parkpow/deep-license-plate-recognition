import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Removes images that are over xx hours in Stream folder."
    )
    parser.add_argument(
        "--threshold",
        choices=range(1, 24),
        metavar="[1-23]",
        help="Time duration (in hours) to remove images older than xx hours",
        type=int,
        required=True,
    )
    return parser.parse_args()


# Function to delete image files
def delete_images(directory, threshold_minutes):
    now = datetime.now()
    threshold_time = now - timedelta(minutes=threshold_minutes)

    for file_path in Path(directory).rglob("*.jpg"):
        modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        if modified_time < threshold_time:
            try:
                file_path.unlink()
            except OSError as e:
                print(f"Error deleting images: {e.filename} - {e.strerror}")


# Function to delete empty directories
def delete_empty_directories(directory):
    for dir_path in reversed(list(Path(directory).rglob("*"))):
        if dir_path.exists() and dir_path.is_dir():
            try:
                if not list(dir_path.iterdir()):
                    dir_path.rmdir()
            except OSError as e:
                print(f"Error deleting empty directories: {e.filename} - {e.strerror}")


def main():
    args = parse_arguments()

    threshold_minutes = args.threshold * 60
    stream_directory = os.path.abspath(os.path.dirname(__file__))

    delete_images(stream_directory, threshold_minutes)
    delete_empty_directories(stream_directory)


if __name__ == "__main__":
    main()
