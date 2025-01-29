import argparse
import os
from pathlib import Path

from docker.client import DockerClient

client = DockerClient.from_env()

paths_to_copy = [
    Path("/app"),
    Path("/usr/local/lib/python3.8/site-packages/"),
    Path("/usr/local/lib/python3.8/dist-packages/"),
]


def extract_updates(args):
    container = client.containers.run(
        args.image, command="/bin/bash", tty=True, detach=True, remove=True
    )
    os.makedirs(args.output, exist_ok=True)
    for path in paths_to_copy:
        zip_file = f"{args.output}/{path.name}.tar"
        with open(zip_file, "wb") as fp:
            bits, stat = container.get_archive(path)
            print(stat)
            for chunk in bits:
                fp.write(chunk)
        print(f"Successfully created {zip_file}")
    container.stop()


def restore_updates(args):
    container = client.containers.run(
        args.image,
        command="/bin/bash",
        tty=True,
        detach=True,
        remove=True,
        working_dir="/",
    )
    for path in paths_to_copy:
        update_file = f"{path.name}.tar"
        with open(args.output / update_file, "rb") as fp:
            container.put_archive(str(path.parent), fp.read())
    # Copy source image CMD, entrypoint ENV
    image_config = client.api.inspect_image(args.image)["Config"]
    container.commit(
        "platerecognizer/alpr-stream", args.tag, pause=True, conf=image_config
    )
    container.stop()
    print(f"Updated image is platerecognizer/alpr-stream:{args.tag}")


def main():
    parser = argparse.ArgumentParser(
        prog="stream-sdk-update",
        description="Stream SDK Slight Update",
    )
    # TODO parser.add_argument('-c', '--compatibility', help='Confirm python versions as similar')
    subparsers = parser.add_subparsers(help="Extract/Restore Help")
    parser_a = subparsers.add_parser("extract", help="Extract updates on machine A")
    parser_a.add_argument("-o", "--output", type=Path, help="Folder to extract to")
    parser_a.add_argument("-i", "--image", type=str, help="Docker Image with updates")
    parser_a.set_defaults(func=extract_updates)

    parser_b = subparsers.add_parser("restore", help="Restore on machine B")
    parser_b.add_argument("-o", "--output", type=Path, help="Folder to restore from")
    parser_b.add_argument("-i", "--image", type=str, help="Existing image to update")
    parser_b.add_argument(
        "-t", "--tag", type=str, help="Tag new image", default="latest"
    )
    parser_b.set_defaults(func=restore_updates)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
