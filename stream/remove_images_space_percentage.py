import argparse
import os
import shutil
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Frees up disk space by deleting oldest images when disk usage exceeds a threshold."
    )
    parser.add_argument(
        "--target_free",
        type=int,
        choices=range(1, 100),
        metavar="[1-99]",
        required=True,
        help="Target free space percentage (x%) to reach after cleanup."
    )
    parser.add_argument(
        "--trigger_usage",
        type=int,
        choices=range(1, 100),
        metavar="[1-99]",
        required=True,
        help="Disk usage percentage (y%) that triggers cleanup."
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
        total, used, free = get_disk_usage(directory)
        return (used / total) * 100, (free / total) * 100

def delete_oldest_files(directory, target_free_percent):
    directory_path = Path(directory)
    all_files = sorted(
        directory_path.rglob("*.jpg"),
        key=lambda p: p.stat().st_mtime
    )

    _, current_free_percent = get_percentages(directory)

    print(f"Current free space: {current_free_percent:.2f}%")
    
    for file_path in all_files:
        if current_free_percent >= target_free_percent:
            print(f"Reached target free space: {current_free_percent:.2f}%")
            break
        
        try:
            file_path.unlink()
            print(f"Deleted: {file_path}")
            _, current_free_percent = get_percentages(directory)
        except OSError as e:
            print(f"Error deleting file {file_path}: {e.strerror}")

def main():
    args = parse_arguments()

    directory = os.path.abspath(args.directory)
    target_free = args.target_free
    trigger_usage = args.trigger_usage

    current_used_percent, _ = get_percentages(directory)
    print(f"Disk usage: {current_used_percent:.2f}%")

    if current_used_percent >= trigger_usage:
        print(f"Disk usage exceeded {trigger_usage}%. Starting cleanup...")
        delete_oldest_files(directory, target_free)
        current_used_percent, current_free_percent = get_percentages(directory)
        print(f"Disk usage: {current_used_percent:.2f}%")
        print(f"Current free space: {current_free_percent:.2f}%")
    else:
        print(f"Disk usage is below {trigger_usage}%. No cleanup needed.")

if __name__ == "__main__":
    main()
