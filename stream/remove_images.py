import argparse
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Image cleanup utility: delete old images based on disk usage or age."
    )
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--usage",
        action="store_true",
        help="Trigger disk space cleanup based on usage thresholds."
    )
    mode_group.add_argument(
        "--age",
        action="store_true",
        help="Trigger cleanup of images older than a threshold in hours."
    )
    parser.add_argument(
        "--target_free",
        type=int,
        choices=range(1, 100),
        metavar="[1-99]",
        help="(Usage mode) Target free space percentage to reach after cleanup."
    )
    parser.add_argument(
        "--trigger_usage",
        type=int,
        choices=range(1, 100),
        metavar="[1-99]",
        help="(Usage mode) Disk usage percentage that triggers cleanup."
    )
    parser.add_argument(
        "--threshold",
        choices=range(1, 24),
        metavar="[1-23]",
        help="Time duration (in hours) to remove images older than xx hours",
        type=int,
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=".",
        help="Directory to clean (default: current directory)."
    )
    return parser.parse_args()
    
def get_disk_usage(path):
    """Returns disk usage stats: (total, used, free) in bytes."""
    usage = shutil.disk_usage(path)
    return usage.total, usage.used, usage.free

def get_percentages(directory):
    """Returns disk usage (used and free) stats in percentages: (used, free) in %."""
    total, used, free = get_disk_usage(directory)
    if total == 0:
        raise ValueError(f"Invalid disk usage: total space is zero for directory '{directory}'")
    return (used / total) * 100, (free / total) * 100

def delete_image(file_path):
    file_size = file_path.stat().st_size
    file_path.unlink()
    print(f"Deleted: {file_path} ({file_size} bytes)")
    
def delete_images_by_percentage(directory, target_free_percent, batch_size=10):
    directory_path = Path(directory)
    all_files = sorted(
        directory_path.rglob("*.jpg"),
        key=lambda p: p.stat().st_mtime
    )

    _, current_free_percent = get_percentages(directory)
    print(f"Current free space: {current_free_percent:.2f}%")

    files_deleted = 0
    
    for file_path in all_files:
        if current_free_percent >= target_free_percent:
            print(f"Reached target free space: {current_free_percent:.2f}%")
            break
        try:
            delete_image(file_path)
            files_deleted += 1
        except OSError as e:
            print(f"Error deleting file {file_path}: {e.strerror}")

        if files_deleted % batch_size == 0:
            _, current_free_percent = get_percentages(directory)
            
    _, current_free_percent = get_percentages(directory)
    print(f"Final free space after deletion: {current_free_percent:.2f}%")


# Function to delete image files
def delete_images_by_age(directory, threshold_minutes):
    now = datetime.now()
    threshold_time = now - timedelta(minutes=threshold_minutes)
    files_deleted = 0
    
    for file_path in Path(directory).rglob("*.jpg"):
        modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        if modified_time < threshold_time:
            try:
                delete_image(file_path)
                files_deleted += 1
            except OSError as e:
                print(f"Error deleting images: {e.filename} - {e.strerror}")
    
    if files_deleted == 0:
        print(f"No file(s) to delete below the threshold time")
        
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
    directory = os.path.abspath(args.directory)

    if args.usage:
        if args.target_free is None or args.trigger_usage is None:
            print("Error: --target_free and --trigger_usage are required in --usage mode.")
            return
        current_used_percent, _ = get_percentages(directory)
        print(f"Disk usage: {current_used_percent:.2f}%")
        if current_used_percent >= args.trigger_usage:
            print(f"Disk usage exceeded {args.trigger_usage}%. Starting cleanup...")
            delete_images_by_percentage(directory, args.target_free)
            delete_empty_directories(directory)
        else:
            print(f"Disk usage is below {args.trigger_usage}%. No cleanup needed.")

    elif args.age:
        if args.threshold is None:
            print("Error: --threshold is required in --age mode.")
            return
        threshold_minutes = args.threshold * 60
        delete_images_by_age(directory, threshold_minutes)
        delete_empty_directories(directory)

if __name__ == "__main__":
    main()
