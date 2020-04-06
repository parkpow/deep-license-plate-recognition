import argparse
import json
import os
import queue
import threading
import time
import uuid
from argparse import RawTextHelpFormatter
from datetime import datetime
from pathlib import Path

try:
    from watchdog.events import PatternMatchingEventHandler
    from watchdog.observers import Observer
except ImportError:
    print('A dependency is missing. Please install: '
          'https://pythonhosted.org/watchdog/installation.html')
    exit(1)

try:
    import requests
except ImportError:
    print('A dependency is missing. Please install: '
          'https://2.python-requests.org/en/master/user/install/#install')
    exit(1)

try:
    import jsonlines
except ImportError:
    print('A dependency is missing. Please install: '
          'https://jsonlines.readthedocs.io/en/latest/#installation')
    exit(1)

_queue = queue.Queue(256)  # type: ignore

##########################
# Command line arguments #
##########################


def parse_arguments():
    parser = argparse.ArgumentParser(description="""
Important! Before starting the image transfer:
  1) Make sure to start the SDK.
  2) Get your ParkPow API token from: https://app.parkpow.com/accounts/token (optional if using parkpow)
  3) Get your PlateRecognizer API token from: https://app.platerecognizer.com/start/ (optional if using Cloud instead of local SDK)


Here is an example of how to call this script if using Local SDK:
python transfer.py --source /home/alpr/camera-images/ --archive /home/alpr/archived-images/ --alpr-api http://localhost:8080/v1/plate-reader/ --parkpow-token MY_TOKEN --cam-pos 2

Example of how to call this script is using the Cloud Api
python transfer.py --source /home/alpr/camera-images/ --archive /home/alpr/archived-images/ --alpr-api https://api.platerecognizer.com/v1/plate-reader/ --platerec-token MY_PLATEREC_TOKEN --parkpow-token MY_TOKEN --cam-pos 2


The path of each image must contain a directory with the camera name.
It is specified with the --cam-pos argument.
Once processed, images are moved to the archive directory.
If it the --api-url is not defined, the results will be saved in the output file --output-file
    """,
                                     formatter_class=RawTextHelpFormatter)

    parser.add_argument('--source',
                        help='Where camera images are saved.',
                        type=str,
                        required=True)
    parser.add_argument(
        '--archive',
        help='Where images are moved to archive after being processed.',
        type=str,
        required=True)
    parser.add_argument('--parkpow-token',
                        help='API token for ParkPow.',
                        type=str,
                        required=False)

    parser.add_argument('--platerec-token',
                        help='API token for PlateRecognizer.',
                        type=str,
                        required=False)
    parser.add_argument(
        '--cam-pos',
        help=
        'Position of the directory with camera name (.../4/3/2/1/image.jpg).\n'
        'For example, with /home/export/parking/camera/july/image.jpg, set --cam-pos=2',
        type=int,
        required=True)

    parser.add_argument('--workers',
                        help='Number of worker threads.',
                        type=int,
                        default=2)
    parser.add_argument(
        '--alpr-api',
        help='URL of Cloud/SDK API.',
        default='https://api.platerecognizer.com/v1/plate-reader')

    parser.add_argument('--use-parkpow',
                        help='Upload results to ParkPow',
                        action='store_true')

    parser.add_argument('--output-file',
                        help="Json file with response",
                        type=str,
                        required=False)

    return parser.parse_args()


##################
# Process images #
##################


def image_transfer(src_path, args):
    split = Path(src_path).parts
    # make this better
    if args.cam_pos >= len(split):
        print('Image path does not match template. Call with -h to see help.')
        return

    filename = split[-1]
    camera = split[-args.cam_pos - 1]
    results = alpr(src_path, args)
    if not results:
        return

    if not args.output_file:

        payload = {
            "results": json.dumps(results),
            "camera": camera,
        }
        files = {
            'image': (filename, open(src_path,
                                     'rb'), 'application/octet-stream')
        }
        response = api_request(args, payload, files)
        if not response:
            return
    else:

        with jsonlines.open(args.output_file, mode='a') as json_file:
            json_file.write(results)
            response = results

    # Move to archive
    archive_dir = '{0}/{1}/{2:%Y}/{2:%m}/{2:%d}'.format(args.archive, camera,
                                                        datetime.now())

    destination = '{}/{}={}'.format(archive_dir, uuid.uuid4(), filename)
    try:
        Path(archive_dir).mkdir(parents=True, exist_ok=True)
        os.rename(src_path, destination)
    except (PermissionError, OSError):
        print('%s could not be moved to archive folder.' % src_path)
    return dict(dest=destination, response=response)


def alpr(path, args):
    print('Sending %s' % path)
    try:
        if 'localhost' in args.alpr_api:
            time.sleep(1)  # Wait for the whole image to arrive
            with open(path, 'rb') as fp:
                response = requests.post(args.alpr_api,
                                         files=dict(upload=fp),
                                         timeout=10)
        else:
            time.sleep(1)  # Wait for the whole image to arrive
            filename = os.path.basename(path)
            response = requests.post(
                args.alpr_api,
                files=dict(upload=(filename, open(path, 'rb'),
                                   'application/octet-stream')),
                headers={'Authorization': 'Token ' + args.platerec_token})

    except requests.exceptions.Timeout:
        print('SDK: Timeout')
        return
    except ConnectionError:
        print('SDK: ConnectionError')
        return
    except PermissionError:
        print('SDK: %s could not be read.' % path)
        return
    except Exception as e:
        print(e)
        return
    data = response.json()
    # TODO: skip data if there is no change
    if 'results' not in data:
        print(data)
        return []
    return data['results']


def api_request(args, payload, files):
    api_url = 'https://app.parkpow.com/api/v1/log-vehicle'
    headers = {'Authorization': 'Token {}'.format(args.parkpow_token)}
    try:
        response = requests.post(api_url,
                                 data=payload,
                                 headers=headers,
                                 files=files,
                                 timeout=20)
    except ConnectionError:
        print('ParkPow API: ConnectionError')
        return
    except requests.exceptions.Timeout:
        print('ParkPow API: Timeout')
        return
    return response


###################
# File monitoring #
###################


def worker(args):
    while True:
        image_transfer(_queue.get(), args)
        _queue.task_done()


class Handler(PatternMatchingEventHandler):

    def on_created(self, event):
        try:
            _queue.put(event.src_path)
        except queue.Full:
            print('Queue is full. Skipping %s.' % event.scr_path)


def main(args, debug=False):
    if args.source in args.archive:
        print('Archive argument should not be in source directory.')
        return exit(1)
    observer = Observer()
    observer.schedule(Handler(ignore_directories=True,
                              patterns='*.jpg *.jpeg'.split()),
                      args.source,
                      recursive=True)
    observer.start()
    for _ in range(args.workers):
        t = threading.Thread(target=worker, args=(args,))
        t.daemon = True
        t.start()

    print('Monitoring source directory.')
    try:
        while True:
            time.sleep(1 if debug else .25)
            if debug:
                break
    except KeyboardInterrupt:
        pass
    print('Closing...')
    observer.stop()
    observer.join()
    _queue.join()


def validate_env(args):
    messages = []
    Path(args.archive).mkdir(parents=True, exist_ok=True)
    if not Path(args.archive).exists():
        messages.append('%s does not exist.' % args.archive)
    if not Path(args.source).exists():
        messages.append('%s does not exist.' % args.source)

    if not args.use_parkpow and not args.output_file:
        messages.append(
            "Pass argument --use-parkpow or the argument --output-file")
    if 'http' not in args.alpr_api:
        messages.append("--alpr-api is not a valid URL")
    if 'api.platerecognizer.com' in args.alpr_api and not args.platerec_token:
        messages.append(
            "Missing argument --platerec-token or SDK argument --alpr-api")

    elif 'api.platerecognizer.com' not in args.alpr_api:
        try:
            response = requests.get(args.alpr_api.rsplit('/v1', 1)[0],
                                    timeout=2)
        except Exception:
            response = None
        if not response or response.status_code != 200:
            messages.append('Make sure that the SDK is up and running (%s).' %
                            args.alpr_api)
    if args.use_parkpow:
        api_url = 'https://app.parkpow.com/api/v1/log-vehicle'
        try:
            response = requests.get(api_url.rsplit('/', 1)[0] + '/parking-list',
                                    headers={
                                        'Authorization':
                                        'Token {}'.format(args.parkpow_token)
                                    },
                                    timeout=2)
        except Exception:
            response = None
        if not response or response.status_code != 200:
            messages.append(response.json(
            ) if response else 'Parkpow server could not be reached.')
    if len(messages) > 0:
        print('Script initialization failed:')
        print('\n'.join(messages))
        print('Exiting...')
        exit(1)


if __name__ == "__main__":
    args = parse_arguments()
    validate_env(args)
    main(args)
