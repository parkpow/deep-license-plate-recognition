import argparse
import math
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from timeit import default_timer

import requests
from psutil import cpu_percent, process_iter


def parse_arguments():
    parser = argparse.ArgumentParser(description="Benchmark Stream.")
    parser.add_argument(
        "--stream-url",
        help="Url to Stream App  For example, http://localhost:80",
        default="http://localhost:80",
    )
    parser.add_argument("--video", default="assets/cars.mp4")
    parser.add_argument("--iterations", default=5, type=int)
    return parser.parse_args()


def print_table(results):
    if not results:
        return
    print("| Speed   | l_min  | l_max  |")
    print("| ------- | ------ | ------ |")
    for result in results:
        print("| {avg:7.1f} | {min:6.1f} | {max:6.1f} |".format(**result))


def stream_api(fp, stream_url, exit_on_error=True):
    fp.seek(0)
    response = requests.post(stream_url, files=dict(upload=fp))
    if response is None:
        return {}
    if response.status_code < 200 or response.status_code > 300:
        print(response.text)
        if exit_on_error:
            exit(1)
    return response.json(object_pairs_hook=OrderedDict)


def call_duration(path, stream_url):
    now = default_timer()
    with open(path, "rb") as fp:
        stream_api(fp, stream_url=stream_url)
    return (default_timer() - now) * 1000


def benchmark(args, executor):
    now = default_timer()
    stats = list(
        executor.map(
            partial(call_duration, stream_url=args.stream_url),
            [args.video] * args.iterations,
        )
    )
    duration = (default_timer() - now) * 1000
    yield dict(
        min=min(stats),
        max=max(stats),
        avg=duration / args.iterations,
    )


def mem_usage():
    usage = {}
    for process in process_iter():
        if "main.py" in process.cmdline() or "start.sh" in process.cmdline():
            usage[process.pid] = process.memory_info()
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
    with ThreadPoolExecutor(max_workers=1) as executor:
        # Warmup
        list(
            executor.map(
                partial(call_duration, stream_url=args.stream_url),
                [args.video],
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
