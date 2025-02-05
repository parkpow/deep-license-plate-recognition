import argparse
import hashlib
import tarfile
import tempfile
from pathlib import Path

from docker.client import DockerClient

client = DockerClient.from_env()

paths_to_copy = [
    Path("/app"),
    Path("/usr/local/lib/python3.8/site-packages/"),
    Path("/usr/local/lib/python3.8/dist-packages/"),
]


def get_python_version(image):
    config = client.api.inspect_image(image)["Config"]
    for env in config["Env"]:
        name, value = env.split("=", maxsplit=1)
        if name == "PYTHON_VERSION":
            return value


def archive_image_updates(image, output) -> str | None:
    container = None
    try:
        container = client.containers.run(
            image, command="/bin/bash", tty=True, detach=True, remove=True
        )

        for path in paths_to_copy:
            zip_file = f"{output}/{path.name}.tar"
            with open(zip_file, "wb") as fp:
                bits, stat = container.get_archive(path)
                print(stat)
                for chunk in bits:
                    fp.write(chunk)
            print(f"Successfully created {zip_file}")
        return get_python_version(image)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
    finally:
        if container is not None:
            container.stop()


def hash_file(filepath):
    """Calculate the SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_tar(tar_path: Path, extract_to: Path):
    """Extract tar file to a specified directory."""
    with tarfile.open(tar_path, "r") as tar:
        tar.extractall(extract_to)


def create_diff_tar(source_tar, destination_tar, output_tar):
    """Create a tar file containing only new or updated files from source_tar compared to destination_tar."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_dir = Path(tmpdirname)
        source_dir = temp_dir / "source"
        source_dir.mkdir(exist_ok=True)
        destination_dir = temp_dir / "destination"
        destination_dir.mkdir(exist_ok=True)

        extract_tar(source_tar, source_dir)
        extract_tar(destination_tar, destination_dir)

        diff_files = []

        for root, _, files in source_dir.walk(on_error=print):
            for file in files:
                source_file_path = root / file
                relative_path = source_file_path.relative_to(source_dir)
                destination_file_path = destination_dir / relative_path

                if not destination_file_path.exists() or hash_file(
                    source_file_path
                ) != hash_file(destination_file_path):
                    diff_files.append(relative_path)

        with tarfile.open(output_tar, "w") as tar:
            for file in diff_files:
                full_path = source_dir / file
                tar.add(full_path, arcname=file)


def extract_updates(args):
    source_image_fs = args.output / "source"
    dest_image_fs = args.output / "dest"
    source_image_fs.mkdir(exist_ok=True)
    dest_image_fs.mkdir(exist_ok=True)

    # Download Source Image Files
    source_python = archive_image_updates(args.source, source_image_fs)
    # Download Source Image Files
    dest_python = archive_image_updates(args.dest, dest_image_fs)
    if source_python != dest_python:
        print(
            "WARNING! Update across different python version is not guaranteed to work."
            f"You are updating from [{source_python}] to [{dest_python}]"
        )
    diff_fs = args.output / "diff"
    diff_fs.mkdir(exist_ok=True)

    for path in paths_to_copy:
        create_diff_tar(
            source_image_fs / f"{path.name}.tar",
            dest_image_fs / f"{path.name}.tar",
            diff_fs / f"{path.name}.tar",
        )


def restore_updates(args):
    container = None
    try:
        container = client.containers.run(
            args.dest,
            command="/bin/bash",
            tty=True,
            detach=True,
            remove=True,
            working_dir="/",
        )
        for path in paths_to_copy:
            # TODO Delete no-longer existing files from container
            update_file = f"{path.name}.tar"
            with open(args.source / update_file, "rb") as fp:
                container.put_archive(str(path.parent), fp.read())
        # Copy source image CMD, entrypoint ENV
        image_config = client.api.inspect_image(args.dest)["Config"]
        container.commit(
            "platerecognizer/alpr-stream", args.output, pause=True, conf=image_config
        )
        print(f"Updated image is platerecognizer/alpr-stream:{args.output}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if container is not None:
            container.stop()


def main():
    parser = argparse.ArgumentParser(
        prog="stream-sdk-update",
        description="Stream SDK Slight Update",
    )
    subparsers = parser.add_subparsers(help="Extract/Restore Help")
    parser_a = subparsers.add_parser("extract", help="Extract updates on machine A")
    parser_a.add_argument(
        "-s", "--source", type=str, help="Docker Image Tag with updates"
    )
    parser_a.add_argument("-d", "--dest", type=str, help="Docker Image Tag to update")
    parser_a.add_argument("-o", "--output", type=Path, help="Folder to extract to")
    parser_a.set_defaults(func=extract_updates)

    parser_b = subparsers.add_parser("restore", help="Restore on machine B")
    parser_b.add_argument("-s", "--source", type=Path, help="Folder to restore from")
    parser_b.add_argument("-d", "--dest", type=str, help="Existing image Tag to update")
    parser_b.add_argument(
        "-o",
        "--output",
        type=str,
        help="New Docker Image Tag With the Updates",
        default="latest",
    )
    parser_b.set_defaults(func=restore_updates)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
