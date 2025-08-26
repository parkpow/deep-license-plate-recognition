import os
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path
from ssl import SSLError

from stream_config import DEFAULT_CONFIG, base_config

try:
    from urllib.error import URLError
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, URLError, urlopen  # type: ignore


def get_os():
    os_system = platform.system()
    if os_system == "Windows":
        return "Windows"
    elif os_system == "Linux":
        return "Linux"
    elif os_system == "Darwin":
        return "Mac OS"
    return os_system


class DockerPermissionError(Exception):
    pass


def verify_docker_install():
    try:
        subprocess.check_output(
            "docker info".split(), stderr=subprocess.STDOUT
        ).decode()
        return True
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()
        perm_error = "Got permission denied while trying to connect"
        if perm_error in output:
            raise DockerPermissionError(output) from exc
        return False


def get_container_id(image):
    cmd = f"docker ps -q --filter ancestor={image}"
    output = subprocess.check_output(cmd.split())
    return output.decode()


def stop_container(image):
    container_id = get_container_id(image)
    if container_id:
        cmd = f"docker stop {container_id}"
        os.system(cmd)
    return container_id


def get_home(product="stream"):
    return str(Path.home() / product)


def get_image(image):
    images = (
        subprocess.check_output(
            ["docker", "images", "--format", '"{{.Repository}}:{{.Tag}}"', image]
        )
        .decode()
        .split("\n")
    )
    return images[0].replace('"', "")


def pull_docker(image):
    if get_container_id(image):
        stop_container(image)
    pull_cmd = f"docker pull {image}"
    os.system(pull_cmd)


def read_config(home):
    try:
        config = Path(home) / "config.ini"
        conf = ""
        f = open(config)
        for line in f:
            conf += line
        f.close()
        return conf
    except OSError:  # file not found
        return DEFAULT_CONFIG


def write_config(home, config):
    try:
        path = Path(home) / "config.ini"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        result, error = base_config(path, config)
        if error:
            return False, error
        with open(path, "w+") as conf:
            for line in config:
                conf.write(line)
        return True, ""
    except Exception:
        return (
            False,
            f"The Installation Directory is not valid. Please enter a valid folder, such as {get_home()}",
        )


def verify_token(token, license_key, get_license=True, product="stream"):
    path = "stream/license" if product == "stream" else "sdk-webhooks"
    if not (token and license_key):
        return False, "API token and license key is required."
    try:
        req = Request(
            "https://api.platerecognizer.com/v1/{}/{}/".format(
                path, license_key.strip()
            )
        )
        req.add_header("Authorization", f"Token {token.strip()}")
        urlopen(req).read()
        return True, None
    except SSLError:
        req = Request(
            f"http://api.platerecognizer.com/v1/{path}/{license_key.strip()}/"
        )
        req.add_header("Authorization", f"Token {token.strip()}")
        urlopen(req).read()
        return True, None
    except URLError as e:
        if "404" in str(e) and get_license:
            return (
                False,
                "The License Key cannot be found. Please use the correct License Key.",
            )
        elif str(403) in str(e):
            return False, "The API Token cannot be found. Please use the correct Token."
        else:
            return True, None


def is_valid_port(port):
    try:
        return 0 <= int(port) <= 65535
    except ValueError:
        return False


def resource_path(relative_path):
    # get absolute path to resource
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def uninstall_docker_image(hardware):
    container_id = get_container_id(hardware)
    if container_id:
        cmd = f"docker container rm {container_id}"
        os.system(cmd)
    cmd = f'docker rmi "{hardware}" -f'
    os.system(cmd)
    cmd = "docker image prune -f"
    os.system(cmd)
    return [None, "Image successfully uninstalled."]


def launch_browser(url):
    os_platform = get_os()
    if os_platform in ["Windows", "Darwin"]:
        return webbrowser.open(url)
    elif os_platform == "Linux":
        opener = "xdg-open"
        # remove all environment variables that contain the 'tmp' directory.
        my_env = dict(os.environ)
        to_delete = []
        for k, v in my_env.items():
            if k != "PATH" and "tmp" in v:
                to_delete.append(k)
        for k in to_delete:
            my_env.pop(k, None)
        try:
            subprocess.call([opener, url], env=my_env, shell=False)
        except (
            FileNotFoundError
        ):  # [Errno 2] No such file or directory: 'xdg-open': 'xdg-open'
            print(f"Unable to launch browser: {opener} command not found")
    else:
        raise Exception(f"Unrecognized OS platform: {os_platform}")
