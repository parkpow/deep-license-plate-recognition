import logging
import requests
from pathlib import Path

from configobj import ConfigObj, flatten_errors
from validate import ValidateError, Validator

DEFAULT_CONFIG = '''# Instructions:
# https://docs.google.com/document/d/1vLwyx4gQvv3gF_kQUvB5sLHoY0IlxV5b3gYUqR2wN1U/edit

# List of TZ names on https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
timezone = UTC

[cameras]
  # Full list of regions: http://docs.platerecognizer.com/#countries
  # regions = fr, gb

  # Sample 1 out of X frames. A high number will result in less compute.
  # A low number is preferred for a stream with fast moving vehicles
  # sample = 2

  # Maximum delay in seconds before a prediction is returned
  # max_prediction_delay = 6

  # Maximum time in seconds that a result stays in memory
  # memory_decay = 300

  # Enable make, model and color prediction. Your account must have that option.
  # mmc = true

  # Image file name, you can use any format codes from https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
  image_format = $(camera)_screenshots/%y-%m-%d/%H-%M-%S.%f.jpg

  # Webhook image type. Use "vehicle" to send only the vehicle image or "original" to
  # send the full-size image. This setting can be used at the camera level too.
  webhook_image_type = vehicle

  [[camera-1]]
    active = yes
    url = rtsp://192.168.0.108:8080/video/h264
    name = Camera One

    # Output methods. Uncomment/comment line to enable/disable.
    # - Save to CSV file. The corresponding frame is stored as an image in the same directory.
    csv_file = $(camera)_%y-%m-%d.csv

    # - Send to Webhook. The recognition data and vehicle image are encoded in
    # multipart/form-data and sent to webhook_target.
    # webhook_target = http://webhook.site/
    # webhook_image = yes

    # - Save to file in JSONLines format. https://jsonlines.org/
    # jsonlines_file = $(camera)_%y-%m-%d.jsonl

'''


def base_config(config_path: Path, config=None):
    global_params = dict(
        regions='force_list(default=list())',
        webhook_target='string(default="")',
        webhook_header='header(default="", url=webhook_target)',
        webhook_image='boolean(default=yes)',
        webhook_image_type='option("vehicle", "original", default="vehicle")',
        max_prediction_delay='float(default=6)',
        memory_decay='float(default=300)',
        image_format=
        'string(default="$(camera)_screenshots/%y-%m-%d/%H-%M-%S.%f.jpg")',
        sample='integer(default=2)',
        total='integer(default=-1)',
        mmc='boolean(default=no)',
        csv_file='string(default="")',
        jsonlines_file='string(default="")',
    )

    camera = dict(
        url='string',
        name='string',
        active='boolean(default=yes)',
        # Overridable
        regions='force_list(default=None)',
        webhook_target='string(default=None)',
        webhook_header='header(default=None, url=webhook_target)',
        webhook_image='boolean(default=None)',
        webhook_image_type='option("vehicle", "original", default=None)',
        max_prediction_delay='float(default=None)',
        memory_decay='float(default=None)',
        image_format='string(default=None)',
        sample='integer(default=None)',
        total='integer(default=None)',
        mmc='boolean(default=None)',
        csv_file='string(default=None)',
        jsonlines_file='string(default=None)',
    )

    def webhook_header_check(value, *args, **kwargs):
        token = value.split('Token ')[-1]
        if not token:
            return None
        url = 'https://app.parkpow.com/api/v1/parking-list'
        headers = {'Authorization': f'Token {token}'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
        except (requests.Timeout, requests.ConnectionError):
            raise ValidateError('Please check your internet connection.')
        if response.status_code != 200:
            raise ValidateError('Wrong token.')
        return value

    spec = ConfigObj()
    spec['timezone'] = 'string(default="UTC")'
    spec['version'] = 'integer(default=2)'
    spec['cameras'] = dict(__many__=camera, **global_params)
    if not config_path.exists():
        with open(config_path, 'w') as fp:
            fp.write(DEFAULT_CONFIG.replace('\n', '\r\n'))
    try:
        config = ConfigObj(config.split('\n') if config else str(config_path),
                           configspec=spec,
                           raise_errors=True,
                           indent_type='  ')
        config.newlines = '\r\n'  # For Windows
    except Exception as e:
        logging.error(e)
        return None, str(e)
    validator = Validator({'header': webhook_header_check})
    result = config.validate(validator, preserve_errors=True)
    errors = flatten_errors(config, result)
    if errors:
        error_message = 'Config errors:'
        for section_list, key, error in errors:
            if error is False:
                error = 'key %s is missing.' % key
            elif key is not None:
                section_list.append(key)
            section_string = '/'.join(section_list)
            logging.error('%s: %s', section_string, error)
            error = f'{section_string}, param: {key}, message: {error}'
            error_message += f'\n{error}'
        return None, error_message
    return config, None
