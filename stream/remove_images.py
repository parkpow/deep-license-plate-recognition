import argparse
import os
import platform
from datetime import datetime, timedelta


def valid_threshold(value):
    try:
        ivalue = int(value)
        if ivalue < 1 or ivalue > 23:
            raise ValueError
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(
            "%s is not a valid threshold. Threshold must be an integer between 1 and 23."
            % value
        )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Removes images that are over xx hours in Stream folder."
    )
    parser.add_argument(
        "--threshold",
        help="Time duration (in hours) to remove images older than xx hours",
        type=valid_threshold,
        required=True,
    )
    return parser.parse_args()


# Function to delete image files
def delete_images(directory, threshold_minutes):
    now = datetime.now()
    threshold_time = now - timedelta(minutes=threshold_minutes)

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                file_path = os.path.join(root, file)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if modified_time < threshold_time:
                    os.remove(file_path)


# Function to delete empty directories
def delete_empty_directories(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)


def main():
    args = parse_arguments()

    threshold_minutes = args.threshold * 60
    stream_directory = os.getcwd()

    if platform.system() == "Windows":
        stream_directory = os.path.abspath(stream_directory)

    delete_images(stream_directory, threshold_minutes)
    delete_empty_directories(stream_directory)


if __name__ == "__main__":
    main()
