#!/usr/bin/env python
import argparse
import ftplib
import json
import logging
import os
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timedelta
from ftplib import FTP, error_perm, error_reply
from typing import Any

import paramiko

from plate_recognition import recognition_api, save_results

LOG_LEVEL = os.environ.get("LOGGING", "INFO").upper()

logging.basicConfig(
    stream=sys.stdout,
    level=LOG_LEVEL,
    style="{",
    format="{asctime} {levelname} {name} {threadName} : {message}",
)

lgr = logging.getLogger(__name__)


def get_files_and_dirs(
    func: Callable[[Any, list, list, list], None]
) -> Callable[[Any], tuple[list, list, list]]:
    def wrapper(self):
        file_list = self.list_files()
        dirs = []
        nondirs = []
        func(self, file_list, dirs, nondirs)
        return file_list, dirs, nondirs

    return wrapper


class FileTransferProcessor(ABC):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.processed = []

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def delete_file(self, file):
        pass

    @abstractmethod
    def list_files(self):
        pass

    @abstractmethod
    def set_ftp_binary_file(self):
        pass

    @abstractmethod
    def set_working_directory(self, path):
        pass

    @abstractmethod
    def get_working_directory(self):
        pass

    @abstractmethod
    def retrieve_files(self):
        pass

    def processing_single_camera(self, args):
        self.set_working_directory(args.folder)

        file_list, dirs, nondirs = self.retrieve_files()

        logging.info(
            "Found %s file(s) in %s.", len(nondirs), self.get_working_directory()
        )

        # processing files
        self.process_files(nondirs)

        for folder in dirs:
            folder_path = f"./{folder}"
            self.camera_id = folder
            self.set_working_directory(folder_path)
            nondirs = []
            file_list = self.list_files()

        for info in file_list:
            name = info[-1]
            ls_type = info[0] if self.os_linux else info[-2]
            if ls_type.startswith("d") or ls_type == "<DIR>":
                # Don't process files any deeper
                pass
            else:
                if self.os_linux:
                    nondirs.append(
                        [name, self.parse_date(info[-4], info[-3], info[-2])]
                    )
                else:
                    file_date = info[0].split("-")
                    file_time = info[1]

                    if "AM" in file_time or "PM" in file_time:
                        parsed_time = datetime.strptime(file_time, "%I:%M%p")
                        file_time = parsed_time.strftime(
                            "%H:%M"
                        )  # from AM/PM to 24-hour format

                    nondirs.append(
                        [
                            name,
                            self.parse_date(
                                file_date[0], file_date[1], file_time, linux=False
                            ),
                        ]
                    )

        logging.info(
            "Found %s file(s) in %s.", len(nondirs), self.get_working_directory()
        )
        self.process_files(nondirs)

    def track_processed(self):
        """
        Track processed is an interval specified

        :param self: FileTransferProcessor properties context
        :return: Boolean
        """
        return self.interval and self.interval > 0 and not self.delete

    def manage_processed_file(self, file, last_modified):
        """
        Process a file path:
        1. Deletes old file in ftp_files from  ftp_client

        :param file: file data path
        :param last_modified: last modified datetime
        """

        rm_older_than_date = datetime.now() - timedelta(seconds=self.delete)
        if rm_older_than_date > last_modified:
            result = self.delete_file(file)
            if "error" in result.lower():
                print(f"file couldn't be deleted: {result}")
            else:
                self.processed.remove(file)

    def process_files(self, ftp_files):
        results = []
        for file_last_modified in ftp_files:
            ftp_file = file_last_modified[0]
            last_modified = file_last_modified[1]

            if self.delete is not None:
                self.manage_processed_file(ftp_file, last_modified)
                continue

            logging.info(ftp_file)

            with tempfile.NamedTemporaryFile(
                suffix="_" + ftp_file, mode="rb+"
            ) as image:

                self.set_ftp_binary_file(ftp_file, image)
                api_res = recognition_api(
                    image,
                    self.regions,
                    self.api_key,
                    self.sdk_url,
                    camera_id=self.camera_id,
                    timestamp=self.timestamp,
                    mmc=self.mmc,
                    exit_on_error=False,
                )
                results.append(api_res)

            if self.track_processed():
                self.processed.append(ftp_file)

        if self.output_file:
            save_results(results, self)
        else:
            print(json.dumps(results, indent=2))

    def get_month_literal(self, month_number):

        month_mapping = {
            "01": "jan",
            "02": "feb",
            "03": "mar",
            "04": "apr",
            "05": "may",
            "06": "jun",
            "07": "jul",
            "08": "aug",
            "09": "sep",
            "10": "oct",
            "11": "nov",
            "12": "dec",
        }

        month_literal = month_mapping.get(month_number.lower(), "unknown")
        return month_literal

    def parse_date(self, x, y, z, linux=True):
        """
        M D T|Y
        Jan 3   1994
        Jan 17  1993
        Sep 13  19:07
        """

        if not linux:
            x = self.get_month_literal(x)

        date_string = f"{x} {int(y):02} {z}"

        if ":" in z:
            modify_year = True
            parse_string = "%b %d %H:%M"
        else:
            modify_year = False
            parse_string = "%b %d %Y"

        logging.debug(f"Input Date String: {date_string}")
        date_time_obj = datetime.strptime(date_string, parse_string)
        if modify_year:
            date_time_obj = date_time_obj.replace(year=datetime.now().year)

        logging.debug(f"Parsed date: {date_time_obj}")
        return date_time_obj


class FTPProcessor(FileTransferProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ftp = None
        self.os_linux = None

    def connect(self):
        self.ftp = FTP(timeout=120)
        self.ftp.connect(self.hostname, self.port)
        self.ftp.login(self.ftp_user, self.ftp_password)
        logging.info(f"Connected to FTP server at {self.hostname}")
        return self.ftp

    def delete_file(self, file):
        try:
            response = self.ftp.delete(file)
            return f"File {file} deleted. Server response: {response}"
        except error_perm as e:
            return f"Permission error: {e}"
        except error_reply as e:
            return f"Other FTP error: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def get_working_directory(self):
        return self.ftp.pwd()

    def set_working_directory(self, path):
        try:
            self.ftp.cwd(path)
        except ftplib.error_perm as e:
            print(f"Error 550: {e}")

    def is_linux_os(self, file_list):
        # check if OS is Linux or Windows
        for info in file_list:
            info_first_possition = info[0]
            if info_first_possition.startswith("d") or info_first_possition.startswith(
                "-"
            ):
                return True
            return False

    def set_ftp_binary_file(self, file, image):
        """Retrieve a file in binary transfer mode

        Args:
            file (String): remote file path
            image (TemporaryFile): image file destination
        """
        self.ftp.retrbinary("RETR " + file, image.write)

    def list_files(self):
        file_list = []
        self.ftp.retrlines("LIST", lambda x: file_list.append(x.split(maxsplit=8)))
        return file_list

    @get_files_and_dirs
    def retrieve_files(self, file_list, dirs, nondirs):
        self.os_linux = self.is_linux_os(file_list)
        for info in file_list:
            name = info[-1]
            ls_type = info[0] if self.os_linux else info[-2]
            if ls_type.startswith("d") or ls_type == "<DIR>":
                dirs.append(name)
            else:
                if self.os_linux:
                    nondirs.append(
                        [name, self.parse_date(info[-4], info[-3], info[-2])]
                    )
                else:
                    file_date = info[0].split("-")
                    file_time = info[1]

                    if "AM" in file_time or "PM" in file_time:
                        parsed_time = datetime.strptime(file_time, "%I:%M%p")
                        file_time = parsed_time.strftime(
                            "%H:%M"
                        )  # from AM/PM to 24-hour format

                    nondirs.append(
                        [
                            name,
                            self.parse_date(
                                file_date[0], file_date[1], file_time, linux=False
                            ),
                        ]
                    )


class SFTPProcessor(FileTransferProcessor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sftp = None
        self.os_linux = True

    def connect(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.ftp_password and not self.pkey:
                print(self.hostname, self.port, self.ftp_user, self.ftp_password)
                ssh.connect(
                    self.hostname,
                    port=self.port,
                    username=self.ftp_user,
                    password=self.ftp_password,
                    look_for_keys=False,
                    allow_agent=False,
                )

            else:
                try:
                    key = paramiko.RSAKey.from_private_key_file(self.pkey)
                    ssh.connect(self.hostname, self.port, self.ftp_user, pkey=key)
                except paramiko.AuthenticationException as e:
                    logging.error(f"Authentication failed: {e}")
                    raise
                except Exception as e:
                    logging.error(f"An unexpected error occurred: {e}")
                    raise

            self.sftp = ssh.open_sftp()
            logging.info(f"Connected to SFTP server at {self.hostname}")

        except paramiko.AuthenticationException:
            logging.error("Authentication failed. Please check your credentials.")
        except paramiko.SSHException as e:
            logging.error(f"SSH connection error: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

        return self.sftp

    def delete_file(self, file):
        try:
            self.sftp.remove(file)
            return f"File {file} deleted."
        except FileNotFoundError as e:
            return f"File not found: {e}"
        except OSError as e:
            return f"An IOError occurred: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

    def get_working_directory(self):
        return self.sftp.getcwd()

    def set_working_directory(self, path):
        try:
            self.sftp.chdir(path)
        except Exception as e:
            print(f"Error changing working directory: {e}")

    def set_ftp_binary_file(self, file, image):
        """Copy a remote file (remotepath) from the SFTP server and write to an open file or file-like object

        Args:
            file (String): remote file path
            image (TemporaryFile): image file destination
        """
        wd = self.get_working_directory()
        self.sftp.getfo(wd + "/" + file, image)

    def list_files(self):

        file_list = []

        try:
            file_list_attr = self.sftp.listdir_attr()

            for attr in file_list_attr:
                file_list.append(str(attr).split())

            for info in file_list:
                # info format: ['-rw-------', '1', '0', '0', '175289', '16', 'Nov', '18:10', 'demo.jpg']
                # adapting to linux standard: ['-rw-------', '1', '0', '0', '175289', 'Nov', '16', '18:10', 'demo.jpg']
                tmp_month = info[-3]
                info[-3] = info[-4]
                info[-4] = tmp_month

        except Exception as e:
            print(f"Error listing files: {e}")
            return

        return file_list

    @get_files_and_dirs
    def retrieve_files(self, file_list, dirs, nondirs):

        for info in file_list:
            name = info[-1]
            if info[0].startswith("d"):
                dirs.append(name)
            else:
                nondirs.append([name, self.parse_date(info[-4], info[-3], info[-2])])


def parse_arguments(args_hook=lambda _: _):
    parser = argparse.ArgumentParser(
        description="Read license plates from the images on an FTP server and output the result as JSON or CSV",
        epilog="""
Examples:\n

FTP:
---
Process images on an FTP server:
ftp_and_sftp_processor.py -a MY_API_KEY -H host -U user1 -P pass
Specify Camera ID and/or two Regions:
ftp_and_sftp_processor.py -a MY_API_KEY -H host -U user1 -P pass -f /home/user1 --camera-id Camera1 -r us-ca -r th-37
Use the Snapshot SDK instead of the Cloud Api:
ftp_and_sftp_processor.py -H host -U user1 -P pass -s http://localhost:8080

""",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("-a", "--api-key", help="Your API key.", required=False)
    parser.add_argument(
        "-r",
        "--regions",
        help="Match the license plate pattern fo specific region",
        required=False,
        action="append",
    )
    parser.add_argument(
        "-s",
        "--sdk-url",
        help="Url to self hosted sdk  For example, http://localhost:8080",
        required=False,
    )
    parser.add_argument(
        "--camera-id", help="Name of the source camera.", required=False
    )

    parser.add_argument(
        "-c",
        "--protocol",
        help="protocol tu use, available choices 'ftp' or 'sftp'",
        choices="ftp sftp".split(),
        default="ftp",
        required=False,
    )

    args_hook(parser)
    args = parser.parse_args()

    if not args.api_key:
        raise Exception("api-key parameter is required")

    return args


def custom_args(parser):
    parser.epilog += """

Specify a folder on the FTP server:
ftp_and_sftp_processor.py -a MY_API_KEY -H 192.168.0.59 -U user1 -P pass -f /home/user1
Delete processed files from the FTP server after 10 seconds:
ftp_and_sftp_processor.py -a MY_API_KEY -H 192.168.0.59 -U user1 -P pass -f /home/user1 -d 10
Specify a folder containing dynamic cameras, Sub-folder names are Camera IDs:
ftp_and_sftp_processor.py -a MY_API_KEY -H 192.168.0.59 -U user1 -P pass --cameras-root /srv/cameras
Periodically check for new files every 10 seconds:
ftp_and_sftp_processor.py -a MY_API_KEY -H 192.168.0.59 -U user1 -P pass -f /home/user1 -i 10
Enable Make Model and Color prediction:
ftp_and_sftp_processor.py -a MY_API_KEY -H 192.168.0.59 -U user1 -P pass -f /home/user1 --mmc
Specify an output file and format for the results:
ftp_and_sftp_processor.py -a MY_API_KEY -H 192.168.0.59 -U user1 -P pass -f /home/user1 -o data.csv --format csv

SFTP:
----
ftp_password login, Process images in /tmp/images:
ftp_and_sftp_processor.py -c sftp -U usr1 -P pass -H 192.168.0.59 -f /tmp/images -a 4805bee#########\n
Private Key login, Process images in /tmp/images:
ftp_and_sftp_processor.py -c sftp -U usr1 --pkey '/home/danleyb2/.ssh/id_rsa' -H 192.168.0.59 -f /tmp/images -a 4805bee#########\n
ftp_password login, Process images in /tmp/images using Snapshot SDK:
ftp_and_sftp_processor.py -c sftp -U usr1  -P pass -H 192.168.0.59 -f /tmp/images -s http://localhost:8080\n
Process images in /tmp/images Periodically every 5 seconds:
ftp_and_sftp_processor.py -c sftp -U usr1  -P pass -H 192.168.0.59 -f /tmp/images -a 4805bee######### -i 5
"""
    parser.add_argument("-t", "--timestamp", help="Timestamp.", required=False)
    parser.add_argument("-H", "--hostname", help="host", required=True)
    parser.add_argument("-p", "--port", help="port", required=False)
    parser.add_argument(
        "-U", "--ftp-user", help="Transfer protocol server user", required=True
    )
    parser.add_argument(
        "-P",
        "--ftp-password",
        help="Transfer protocol server user's password",
        required=False,
    )
    parser.add_argument("--pkey", help="SFTP Private Key Path", required=False)
    parser.add_argument(
        "-d",
        "--delete",
        type=int,
        help="Remove images from the FTP server after processing. Optionally specify a timeout in seconds.",
        nargs="?",
        const=0,
    )
    parser.add_argument(
        "-f",
        "--folder",
        help="Specify folder with images on the FTP server.",
        default="/",
    )
    parser.add_argument(
        "--cameras-root", help="Root folder containing dynamic cameras", required=False
    )
    parser.add_argument("-o", "--output-file", help="Save result to file.")
    parser.add_argument(
        "--format",
        help="Format of the result.",
        default="json",
        choices="json csv".split(),
    )
    parser.add_argument(
        "--mmc",
        action="store_true",
        help="Predict vehicle make and model (SDK only). It has to be enabled.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        help="Periodically fetch new images from the server every interval seconds.",
    )

    def default_port():
        return 21 if parser.parse_args().protocol == "ftp" else 22

    parser.set_defaults(port=default_port())


def ftp_process(args):

    args_dict = vars(args)

    if args.protocol == "ftp":
        file_processor = FTPProcessor(**args_dict)
    else:
        if not args.ftp_password and not args.pkey:
            raise Exception("ftp_password or pkey path are required")
        file_processor = SFTPProcessor(**args_dict)

    """
    for attr, value in file_processor.__dict__.items():
        print(f"{attr}: {value}")
    """

    file_processor.connect()

    if args.cameras_root:
        file_processor.set_working_directory(args.cameras_root)
        file_list, dirs, nondirs = file_processor.retrieve_files()
        for folder in dirs:
            logging.info(
                f"Processing Dynamic Camera : {file_processor.get_working_directory()}"
            )
            args.folder = os.path.join(args.cameras_root, folder)
            # The camera id is the folder name
            args.camera_id = folder

            file_processor.processing_single_camera(args)
    else:
        file_processor.processing_single_camera(args)


def main():
    args = parse_arguments(custom_args)

    if args.interval and args.interval > 0:
        while True:
            try:
                ftp_process(args)
            except Exception as e:
                print(f"ERROR: {e}")
            time.sleep(args.interval)
    else:
        ftp_process(args)


if __name__ == "__main__":
    main()
