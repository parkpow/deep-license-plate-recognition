#!/usr/bin/env python
import argparse
import json
import logging
import tempfile
from ftplib import FTP
import time
import os
from datetime import datetime, timedelta

from plate_recognition import recognition_api, save_results

logging.basicConfig(format='%(message)s', level=logging.INFO)

# Keep track of processed file names
processed = None


def parse_arguments(args_hook=lambda _: _):
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from the images on an FTP server and output the result as JSON or CSV',
        epilog="""Examples:
Process images on an FTP server: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass
Specify Camera ID and/or two Regions: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass -f /home/user1 --camera-id Camera1 -r us-ca -r th-37
Use the Snapshot SDK instead of the Cloud Api: ftp_processor.py --ftp-host host --ftp-user user1 --ftp-password pass -s http://localhost:8080""",
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-a', '--api-key', help='Your API key.', required=False)
    parser.add_argument(
        '-r',
        '--regions',
        help='Match the license plate pattern fo specific region',
        required=False,
        action="append")
    parser.add_argument(
        '-s',
        '--sdk-url',
        help="Url to self hosted sdk  For example, http://localhost:8080",
        required=False)
    parser.add_argument('--camera-id',
                        help="Name of the source camera.",
                        required=False)
    args_hook(parser)
    args = parser.parse_args()
    if not args.sdk_url and not args.api_key:
        raise Exception('api-key is required')
    return args


def custom_args(parser):
    parser.epilog += """
Specify a folder on the FTP server: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass -f /home/user1
Delete processed files from the FTP server after 10 seconds: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass -f /home/user1 -d 10
Specify a folder containing dynamic cameras, Sub-folder names are Camera IDs: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass --cameras-root /srv/cameras
Periodically check for new files every 10 seconds: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass -f /home/user1 -i 10
Enable Make Model and Color prediction: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass -f /home/user1 --mmc
Specify an output file and format for the results: ftp_processor.py -a MY_API_KEY --ftp-host host --ftp-user user1 --ftp-password pass -f /home/user1 -o data.csv --format csv
    """
    parser.add_argument('-t', '--timestamp', help='Timestamp.', required=False)
    parser.add_argument('--ftp-host', help='FTP host', required=True)
    parser.add_argument('--ftp-user', help='FTP user', required=True)
    parser.add_argument('--ftp-password', help='FTP password', required=True)
    parser.add_argument(
        '-d',
        '--delete',
        type=int,
        help=
        'Remove images from the FTP server after processing. Optionally specify a timeout in seconds.',
        nargs='?',
        const=0)
    parser.add_argument('-f',
                        '--folder',
                        help='Specify folder with images on the FTP server.',
                        default='/')
    parser.add_argument('--cameras-root',
                        help='Root folder containing dynamic cameras',
                        required=False)
    parser.add_argument('-o', '--output-file', help='Save result to file.')
    parser.add_argument('--format',
                        help='Format of the result.',
                        default='json',
                        choices='json csv'.split())
    parser.add_argument(
        '--mmc',
        action='store_true',
        help='Predict vehicle make and model (SDK only). It has to be enabled.')
    parser.add_argument(
        '-i',
        '--interval',
        type=int,
        help=
        'Periodically fetch new images from the server every interval seconds.')


def track_processed(args):
    """
    Track processed if there might be a delete timeout or interval specified

    :param args:
    :return:
    """
    return args.delete or (args.interval and args.interval > 0)


def process_files(ftp_client, ftp_files, args):
    """
    Process a list of file paths by:
    1. Deletes old files in ftp_files from  ftp_client
    2. For new files, retrieving the full file from ftp_client
    3. Calling Snapshot API and Tracking Successfully Processed file paths

    :param ftp_client:
    :param ftp_files: List of files in the format [path, modified datetime], usually from a single folder.
    :param args:
    :return:
    """

    results = []

    for file_last_modified in ftp_files:
        ftp_file = file_last_modified[0]
        last_modified = file_last_modified[1]

        if track_processed(args) and ftp_file in processed:
            if args.delete is not None:
                rm_older_than_date = datetime.now() - timedelta(
                    seconds=args.delete)
                if rm_older_than_date > last_modified:
                    ftp_client.delete(ftp_file)
                    processed.remove(ftp_file)

            continue

        logging.info(ftp_file)
        with tempfile.NamedTemporaryFile(suffix='_' + ftp_file,
                                         mode='rb+') as image:
            ftp_client.retrbinary('RETR ' + ftp_file, image.write)
            api_res = recognition_api(image,
                                      args.regions,
                                      args.api_key,
                                      args.sdk_url,
                                      camera_id=args.camera_id,
                                      timestamp=args.timestamp,
                                      mmc=args.mmc,
                                      exit_on_error=False)
            results.append(api_res)

        if track_processed(args):
            processed.append(ftp_file)

    if args.output_file:
        save_results(results, args)
    else:
        print(json.dumps(results, indent=2))


def parse_date(x, y, z):
    """
    M D T|Y
    Jan 3   1994
    Jan 17  1993
    Sep 13  19:07
    """
    date_string = f'{x} {int(y):02} {z}'
    if ':' in z:
        modify_year = True
        parse_string = '%b %d %H:%M'
    else:
        modify_year = False
        parse_string = '%b %d %Y'

    logging.debug(f'Input Date String: {date_string}')
    date_time_obj = datetime.strptime(date_string, parse_string)
    if modify_year:
        date_time_obj = date_time_obj.replace(year=datetime.now().year)

    logging.debug(f'Parsed date: {date_time_obj}')
    return date_time_obj


def retrieve_files(ftp):
    file_list = []
    dirs = []
    nondirs = []

    ftp.retrlines('LIST', lambda x: file_list.append(x.split(maxsplit=8)))

    for info in file_list:
        ls_type, name = info[0], info[-1]
        if ls_type.startswith('d'):
            dirs.append(name)
        else:
            nondirs.append([name, parse_date(info[-4], info[-3], info[-2])])

    return file_list, dirs, nondirs


def single_camera_processing(ftp, args):
    # Switch to the camera's root dir
    ftp.cwd(args.folder)

    file_list = []
    dirs = []
    nondirs = []

    # Process all files in root. Separate folders and files
    file_list, dirs, nondirs = retrieve_files(ftp)
    logging.info('Found %s file(s) in %s.', len(file_list), args.folder)

    # Process files
    process_files(ftp, nondirs, args)

    # Process day folders
    for folder in dirs:
        folder_path = f'{args.folder}/{folder}'
        ftp.cwd(folder_path)
        # This time we asume all are images,
        # so we don't have to check for folder
        file_list = []
        ftp.retrlines('LIST', lambda x: file_list.append(x.split(maxsplit=8)))

        nondirs = []
        for info in file_list:
            ls_type, name = info[0], info[-1]
            if ls_type.startswith('d'):
                # Don't process files any deeper
                pass
            else:
                nondirs.append([name, parse_date(info[-4], info[-3], info[-2])])

        logging.info('Found %s file(s) in %s.', len(nondirs), folder_path)
        process_files(ftp, nondirs, args)


def ftp_process(args):
    ftp = FTP(timeout=120)
    ftp.connect(args.ftp_host)
    ftp.login(args.ftp_user, args.ftp_password)
    logging.info(f'Connected to FTP server at {args.ftp_host}')

    # generate camera IDs from the names of all the folders in root
    if args.cameras_root:
        ftp.cwd(args.cameras_root)

        files, dirs, nondirs = retrieve_files(ftp)
        logging.info(f'Found {len(dirs)} Cameras in : {args.cameras_root}')
        for folder in dirs:
            logging.info(f'Processing Dynamic Camera : {folder}')
            args.folder = os.path.join(args.cameras_root, folder)
            # The camera id is the folder name
            args.camera_id = folder

            single_camera_processing(ftp, args)
    else:
        single_camera_processing(ftp, args)


def main():
    args = parse_arguments(custom_args)
    if args.interval and args.interval > 0:
        global processed
        processed = []
        while True:
            try:
                ftp_process(args)
            except Exception as e:
                print(f'ERROR: {e}')
            time.sleep(args.interval)
    else:
        ftp_process(args)


if __name__ == '__main__':
    main()
