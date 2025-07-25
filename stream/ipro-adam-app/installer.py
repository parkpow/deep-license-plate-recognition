import argparse
import logging
import os
from pathlib import Path

import requests
import tqdm
from requests.auth import HTTPDigestAuth
from requests_toolbelt.multipart.encoder import (
    MultipartEncoder,
    MultipartEncoderMonitor,
)

#  tqdm-4.67.1
#  requests-toolbelt-1.0.0

lgr = logging.getLogger(__name__)


def make_request(method, params=None, data=None, headers=None, use_install_url=False):
    if use_install_url:
        url = f"{camera_url}/cgi-bin/adam_install.cgi"
    else:
        url = f"{camera_url}/cgi-bin/adam.cgi"
    lgr.debug(f"url: {url}")
    lgr.debug(f"headers: {headers}")

    response = requests.request(
        method,
        url,
        params=params,
        data=data,
        headers=headers,
        auth=HTTPDigestAuth(username, password),
    )

    lgr.info(f"response: {response}")
    lgr.debug(f"response: {response.text}")

    return response


def list_applications(name):
    applications = make_request("GET", {"methodName": "getApplicationList"}).json()
    for a in applications["appList"]:
        if a["appInfo"]["appNameList"][0]["name"] == name:
            return a
    return None


def upload_adam_app(ext_file_path):
    """
    Content-Type: multipart/form-data; boundary=----WebKitFormBoundary9dLmSwnFFi6H43X6
    Body Format:
    ------WebKitFormBoundaryKeEUnMHC1xkj75DO
    Content-Disposition: form-data; name="methodName"

    installApplication
    ------WebKitFormBoundaryKeEUnMHC1xkj75DO
    Content-Disposition: form-data; name="applicationPackage"; filename="stream-adam_1.1.ext"
    Content-Type: application/octet-stream

    ------WebKitFormBoundaryKeEUnMHC1xkj75DO--

    :param ext_file_path:
    :return:
    """
    file_size = os.path.getsize(ext_file_path)
    progress_bar = tqdm.tqdm(
        desc=f"Uploading App File:[{ext_file_path}]",
        total=file_size,
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    )

    def progress_callback(monitor):
        # uploaded = monitor.bytes_read
        # total = monitor.len
        progress_bar.update(monitor.bytes_read - progress_bar.n)

    with open(ext_file_path, "rb") as fp:
        try:
            # Construct the multipart body
            encoder = MultipartEncoder(
                fields={
                    "methodName": "installApplication",
                    "applicationPackage": (
                        os.path.basename(ext_file_path),
                        fp,
                        "application/octet-stream",
                    ),
                }
            )
            # Wrap encoder with a monitor for progress tracking
            monitor = MultipartEncoderMonitor(encoder, progress_callback)
            headers = {"Content-Type": monitor.content_type}
            response = make_request(
                "POST", use_install_url=True, data=monitor, headers=headers
            )

            if response.status_code == 204:
                print("Application Installed!!!")
                print(response.headers)
            else:
                print(
                    f"Application Install Failed - status code: {response.status_code}"
                )
                print(response.text)
        except Exception:
            raise


def uninstall(install_id):
    data = {"methodName": "uninstallApplication", "installId": install_id}
    res = make_request("POST", data=data)
    if res.status_code != 200:
        lgr.error(res.text)
    else:
        print("Application Uninstalled!!!")


def stop(install_id):
    params = {"methodName": "stopApplication", "installId": install_id}
    res = make_request("GET", params)

    if res.status_code != 200:
        # {"faultCode":"3","faultString":"Invalid Install ID"}
        lgr.error(res.text)
    else:
        print("Application Stopped!!!")


def start(install_id):
    params = {"methodName": "startApplication", "installId": install_id}
    res = make_request("GET", params)
    if res.status_code != 200:
        # {"faultCode":"3","faultString":"Invalid Install ID"}
        raise Exception(res.text)
    print("Application Started!!!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="AdamAPP Installer",
        description="Quick Install or Replace AdamAPP(.ext) on i-PRO",
        epilog="Upload Adam APP to i-PRO with Progress",
    )

    camera_url = "http://CAMERA_IP:80"
    username = "CAMERA_USERNAME"
    password = "CAMERA_PASSWORD"
    ext_file = "/tmp/app-build-dir/stream-adam_1.1.ext"
    installed_app_name = "Platerecognizer Stream"

    parser.add_argument(
        "--ext-file",
        type=Path,
        default=ext_file,
        help="App ext file to install",
        required=False,
    )
    parser.add_argument(
        "--app-name",
        type=str,
        default=installed_app_name,
        help="app_name after install, used to find app app install ID",
        required=False,
    )
    parser.add_argument(
        "--camera-url",
        type=str,
        default=camera_url,
        help="camera access url including port and scheme",
        required=False,
    )
    parser.add_argument(
        "--username",
        type=str,
        default=username,
        help="username of camera login",
        required=False,
    )
    parser.add_argument(
        "--password",
        type=str,
        default=password,
        help="password of camera login",
        required=False,
    )
    # Add skip param to skip directly to upload
    args = parser.parse_args()
    if username != args.username:
        username = args.username
    if password != args.password:
        password = args.password
    if camera_url != args.camera_url:
        camera_url = args.camera_url

    # list applications
    application = list_applications(args.app_name)
    print(f"Uninstall application: {application}")
    if application is not None:
        app_install_id = application["appInfo"]["installId"]
        # Stop
        stop(app_install_id)
        # Uninstall
        uninstall(app_install_id)

    # Upload new Install
    upload_adam_app(args.ext_file)

    installed_application = list_applications(args.app_name)
    print(f"Installed application: {installed_application}")
    if installed_application:
        app_install_id = installed_application["appInfo"]["installId"]
        # Start Application
        start(app_install_id)
