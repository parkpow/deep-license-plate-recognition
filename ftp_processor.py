import argparse
import json
import logging
import tempfile
from ftplib import FTP
import time
from datetime import datetime, timedelta

from plate_recognition import recognition_api, save_results

logging.basicConfig(format='%(message)s', level=logging.INFO)

# Keep track of processed file names
processed = None


def parse_arguments(args_hook=lambda _: _):
    parser = argparse.ArgumentParser(
        description=
        'Read license plates from the images placed on FTP server and output the result as JSON.',
        epilog='Examples:\n'
        'To send images to our cloud service: '
        'python ftp_processor.py --api-key MY_API_KEY --ftp-host hostname '
        '--ftp-user username --ftp-password password\n',
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
    parser.epilog += 'To process images and save result as json: python ftp_processor.py --sdk-url http://localhost:8080  --ftp-host hostname --ftp-user username --ftp-password password\n'
    parser.add_argument('-t', '--timestamp', help='Timestamp.', required=False)
    parser.add_argument('--ftp-host', help='FTP host.', required=True)
    parser.add_argument('--ftp-user', help='FTP user.', required=True)
    parser.add_argument('--ftp-password', help='FTP password.', required=True)
    parser.add_argument(
        '-d',
        '--delete',
        type=int,
        help=
        'Remove images from the FTP server after processing. Optionally specify a timeout in seconds.',
        default=0)
    parser.add_argument('-f',
                        '--folder',
                        help='Specify folder with images on the FTP server.',
                        default='/')
    parser.add_argument('-o', '--output-file', help='Save result to file.')
    parser.add_argument('--format',
                        help='Format of the result.',
                        default='json',
                        choices='json csv'.split())
    parser.add_argument(
        '-i',
        '--interval',
        type=int,
        help=
        'Periodically fetch new images from the server every interval seconds.')


def process_files(ftp_client, ftp_files, args):

    results = []
    rm_older_than_date = datetime.now() - timedelta(seconds=args.delete)

    for file_last_modified in ftp_files:
        ftp_file = file_last_modified[0]
        last_modified = file_last_modified[1]

        if ftp_file in processed:
            if args.delete:
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
                                      exit_on_error=False)
            results.append(api_res)

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


def ftp_process(args):
    ftp = FTP(timeout=120)
    ftp.connect(args.ftp_host)
    ftp.login(args.ftp_user, args.ftp_password)
    logging.info(f'Connected to FTP server at {args.ftp_host}')
    ftp.cwd(args.folder)
    file_list = []
    dirs = []
    nondirs = []

    # Process all files in root. Separate folders and files
    ftp.retrlines('LIST', lambda x: file_list.append(x.split()))

    for info in file_list:
        ls_type, name = info[0], info[-1]
        if ls_type.startswith('d'):
            dirs.append(name)
        else:
            nondirs.append([name, parse_date(info[-4], info[-3], info[-2])])

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
        ftp.retrlines('LIST', lambda x: file_list.append(x.split()))

        nondirs = []
        for info in file_list:
            print(info)
            ls_type, name = info[0], info[-1]
            if ls_type.startswith('d'):
                # Don't process files any deeper
                pass
            else:
                nondirs.append([name, parse_date(info[-4], info[-3], info[-2])])

        logging.info('Found %s file(s) in %s.', len(nondirs), folder_path)
        process_files(ftp, nondirs, args)


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
