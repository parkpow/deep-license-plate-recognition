import argparse
import math
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import os
from timeit import default_timer

import requests
import subprocess
import time


def parse_arguments():
    parser = argparse.ArgumentParser(description="Benchmark Video Blur")
    parser.add_argument(
        "--video-editor-url", default="http://localhost:8081/process-video"
    )
    parser.add_argument("--sample", default="60,50")
    parser.add_argument("--video", default="assets/cars.mp4")
    parser.add_argument("--blur-output", default="output/cars_blur.mp4")
    parser.add_argument("--benchmark-results", default="benchmark_results.txt")
    return parser.parse_args()


def write_results(args, results):
    file_path = args.benchmark_results

    # Check if the file exists
    file_exists = os.path.exists(file_path)

    # Open the file in append mode if it exists, or create it if it doesn't
    mode = "a" if file_exists else "w"

    with open(file_path, mode) as file:
        if not file_exists:
            file.write(
                "| {:<6} | {:<11} | {:>8} |\n".format(
                    "Sample", "Output Size", "Duration"
                )
            )
            file.write("| ------ | ----------- | -------- |\n")

        # Append or write the results
        for result in results:
            file.write(
                "| {:>6} | {:>11} | {:>8.1f} |\n".format(
                    result["rate"], result["size"], result["duration"]
                )
            )


def print_table(file_path):
    with open(file_path, "r") as file:
        for line in file:
            print(line, end="")


def video_blur_api(fp, video_editor_url, exit_on_error=True):
    fp.seek(0)
    response = requests.post(
        video_editor_url, data=dict(action="blur"), files=dict(upload=fp)
    )
    if response is None:
        return {}
    if response.status_code < 200 or response.status_code > 300:
        print(response.text)
        if exit_on_error:
            exit(1)
    return response.json(object_pairs_hook=OrderedDict)


def call_duration(path, video_editor_url):
    now = default_timer()
    with open(path, "rb") as fp:
        video_blur_api(fp, video_editor_url=video_editor_url)
    return default_timer() - now


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    sign = ""
    if size_bytes < 0:
        size_bytes *= -1
        sign = "-"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{sign}{s} {size_name[i]}"


def benchmark(args, executor, sample_rate):
    stats = list(
        executor.map(
            partial(call_duration, video_editor_url=args.video_editor_url),
            [args.video],
        )
    )
    file_size = os.path.getsize(args.blur_output)
    yield dict(
        rate=sample_rate,
        size=convert_size(file_size),
        duration=max(stats),
    )


def check_api_access(api_url, max_wait_time=60, poll_interval=2):
    """
    Waits for the API endpoint to become accessible within a specified time.

    Args:
        api_url (str): The URL of the API endpoint to check.
        max_wait_time (int): Maximum time to wait in seconds.
        poll_interval (int): Interval for checking the API availability.

    Returns:
        bool: True if the API is accessible within the specified time, False otherwise.
    """
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        try:
            # Try to make an HTTP request to the API endpoint
            response = requests.options(api_url)
            if response.status_code == 200:
                # The API is accessible, return True
                return True
        except requests.exceptions.RequestException:
            pass  # Handle any exceptions if the request fails

        # Wait for the next poll_interval seconds before checking again
        time.sleep(poll_interval)

    # If we reach here, it means the API didn't become accessible within max_wait_time
    return False


def main():
    args = parse_arguments()

    rate_string = args.sample
    number_strings = rate_string.split(",")
    sample_rates = [int(x) for x in number_strings]

    with ThreadPoolExecutor(max_workers=1) as executor:
        for sample_rate in sample_rates:
            # Read the existing env.txt file and remove any existing SAMPLE entry
            lines = []
            with open("env.txt", "r") as env_file:
                for line in env_file:
                    if not line.startswith("SAMPLE="):
                        lines.append(line)

            with open("env.txt", "w") as env_file:
                for line in lines:
                    env_file.write(line)

                # Add the new SAMPLE_RATE entry
                env_file.write(f"SAMPLE={sample_rate}\n")

            # Process the video with the modified environment
            cmd = "docker compose up --build"
            subprocess.Popen(cmd, shell=True)

            if check_api_access(args.video_editor_url):
                print("API is accessible, you can proceed with the benchmark.")
            else:
                print(
                    "API not accessible within the specified time. Take appropriate action."
                )

            # Start Benchmark
            results = list(benchmark(args, executor, sample_rate))

            cmd = "docker compose down"
            subprocess.call(cmd, shell=True)

            # Write benchmark results to file to save progress.
            write_results(args, results)

        print_table(args.benchmark_results)


if __name__ == "__main__":
    main()
