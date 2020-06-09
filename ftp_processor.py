import argparse
import imghdr
import json
import tempfile
from ftplib import FTP

from plate_recognition import recognition_api, save_results


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
        help='Remove images from the FTP server after processing.',
        default=False)
    parser.add_argument('-o', '--output-file', help='Save result to file.')
    parser.add_argument('--format',
                        help='Format of the result.',
                        default='json',
                        choices='json csv'.split())


def main():
    args = parse_arguments(custom_args)

    ftp = FTP()
    ftp.connect(args.ftp_host)
    ftp.login(args.ftp_user, args.ftp_password)
    ftp.cwd('/drivehqshare/marcemile/GroupWrite')
    ftp_files = ftp.nlst()

    results = []

    for ftp_file in ftp_files:
        with tempfile.NamedTemporaryFile(mode='wb') as image:
            ftp.retrbinary(f'RETR {ftp_file}', image.write)
            if imghdr.what(image.name):  # check is it image or not
                with open(image.name, 'rb') as fp:
                    api_res = recognition_api(fp,
                                              args.regions,
                                              args.api_key,
                                              args.sdk_url,
                                              camera_id=args.camera_id,
                                              timestamp=args.timestamp)
                    results.append(api_res)
                if args.delete:
                    ftp.delete(ftp_file)

    if args.output_file:
        save_results(results, args)
    else:
        print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
