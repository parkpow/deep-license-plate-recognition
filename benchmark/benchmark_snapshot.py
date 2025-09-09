import argparse
import math
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from statistics import mean
from timeit import default_timer

import psutil
import requests
from PIL import Image
from psutil import cpu_percent, process_iter

from plate_recognition import recognition_api


def parse_arguments():
    parser = argparse.ArgumentParser(description="Benchmark SDK.")
    parser.add_argument(
        "--sdk-url",
        help="Url to self hosted sdk  For example, http://localhost:8080",
        default="http://localhost:8080",
    )
    parser.add_argument(
        "--threads", help="Use thread to parallelize API calls", default=4, type=int
    )
    parser.add_argument("--image", default="assets/car-4k.jpg")
    parser.add_argument("--mmc", action="store_true")
    parser.add_argument("--iterations", default=50, type=int)
    parser.add_argument("--blur", action="store_true")
    return parser.parse_args()


def print_table(results):
    if not results:
        return
    print("| Mode     | Resolution | Speed   | l_min  | l_max  |")
    print("| -------- | ---------- | ------- | ------ | ------ |")
    for result in results:
        print(
            "| {mode:8s} | {resolution:10s} | {avg:7.1f} | {min:6.1f} | {max:6.1f} |".format(
                **result
            )
        )


def blur_api(url, fp):
    """
    Upload an Image to url for burring
    """
    response = requests.post(url, files={"upload": fp})
    if response.status_code < 200 or response.status_code > 300:
        if response.status_code == 400:
            msg = response.json().get("error")
        else:
            msg = response.text
        raise Exception(f"Error performing blur: {msg}")

    blur_data = response.json().get("blur")
    if blur_data is None:
        raise Exception(
            "Error - ensure blurring on server is enabled - "
            "https://guides.platerecognizer.com/docs/blur/api-reference#post-parameters"
        )
    return blur_data


def call_duration(path, sdk_url, config, mmc, blur):
    now = default_timer()
    with open(path, "rb") as fp:
        if blur:
            blur_api(sdk_url, fp)
        else:
            recognition_api(
                fp, sdk_url=sdk_url, config=config, mmc="true" if mmc else "false"
            )
    return (default_timer() - now) * 1000


def benchmark(args, executor):
    image = Image.open(args.image)
    for resolution in [(800, 600), (1280, 720), (1920, 1080), (2560, 1440), (3840, 2160)]:
        image.resize(resolution).save("/tmp/platerec-benchmark.jpg")
        if args.blur:
            configs = [{}]
        else:
            configs = [{}, dict(mode="fast")]

        for config in configs:
            stats = list(
                executor.map(
                    partial(
                        call_duration,
                        sdk_url=args.sdk_url,
                        config=config,
                        mmc=args.mmc,
                        blur=args.blur,
                    ),
                    ["/tmp/platerec-benchmark.jpg"] * args.iterations,
                )
            )
            yield dict(
                resolution="%sx%s" % resolution,
                mode=config.get("mode", "regular"),
                min=min(stats),
                max=max(stats),
                avg=mean(stats),
            )


def mem_usage():
    usage = {}
    for process in process_iter():
        try:
            if "main.py" in process.cmdline() or "start.sh" in process.cmdline():
                usage[process.pid] = process.memory_info()
        except psutil.ZombieProcess:
            pass
    return usage


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


def main():
    args = parse_arguments()
    initial_mem = mem_usage()
    cpu_percent()  # first time this is called it will return a meaningless 0.0
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        # Warmup
        list(
            executor.map(
                partial(
                    call_duration,
                    sdk_url=args.sdk_url,
                    config={},
                    mmc=args.mmc,
                    blur=args.blur,
                ),
                [args.image] * 2,
            )
        )
        # Benchmark
        results = list(benchmark(args, executor))

    # Memory Usage
    print(f"CPU: {cpu_percent()}%")
    for pid, mem in mem_usage().items():
        print(
            f"PID: {pid:5}, "
            f"RES {convert_size(mem.rss):10} ({convert_size(mem.rss - initial_mem[pid].rss):10}), "
            f"SHR {convert_size(mem.shared):10} ({convert_size(mem.shared - initial_mem[pid].shared):10})"
        )
    print_table(results)


if __name__ == "__main__":
    main()
