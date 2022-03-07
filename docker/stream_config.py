import logging
from pathlib import Path

import requests
from configobj import ConfigObj, flatten_errors
from validate import ValidateError, Validator

DEFAULT_CONFIG = '''# Instructions:
# https://app.platerecognizer.com/stream-docs

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

  # When a webhook is sent, the request will time out after n seconds and retry later.
  # webhook_request_timeout = 30

  # Only accept the results that exactly match the templates of the specified regions.
  # region_config = strict

  # Only accept license plates when a vehicle is also detected.
  # detection_rule = strict

  # Beta - Detect vehicles without a license plate. One of: plate, vehicle
  # detection_mode = plate

  # Advanced - Number of steps used to merge unique vehicles. A low number will increase compute.
  # If set to -1, it is automatically picked (default).
  # merge_buffer = -1

  [[camera-1]]
    active = yes
    url = rtsp://192.168.0.108:8080/video/h264

    # Output methods. Uncomment/comment line to enable/disable.
    # - Save to CSV file. The corresponding frame is stored as an image in the same directory.
    csv_file = $(camera)_%y-%m-%d.csv

    # - Send to Webhook. The recognition data and vehicle image are encoded in
    # multipart/form-data and sent to webhook_target.
    # webhook_targets = http://webhook.site/
    # webhook_image = yes
    # webhook_caching = yes

    # - Send to ParkPow. See https://app.parkpow.com/accounts/token/
    # - Save to file in JSONLines format. https://jsonlines.org/
    # jsonlines_file = $(camera)_%y-%m-%d.jsonl

'''


def send_request(section):
    if not section.get('webhook_target') or not section.get('webhook_header'):
        return
    if '/api/v1/webhook-receiver' not in section['webhook_target']:
        return
    headers = {
        'Authorization':
            'Token %s' % section['webhook_header'].split('Token ')[-1]
    }
    url = section['webhook_target'].replace('webhook-receiver', 'parking-list')
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except (requests.Timeout, requests.ConnectionError):
        raise ValidateError(
            '[STR0019] The value in webhook_target in the config.ini file is incorrect.  '
            'Please check the webhook_target value and try again.  '
            'Go here for additional help '
            'https://guides.platerecognizer.com/docs/stream/configuration#webhook-parameters.'
        )
    if response.status_code != 200:
        raise ValidateError(
            '[STR0020] The Token in webhook_header in the config.ini file is incorrect.  '
            'Please check the webhook_header value and try again.  '
            'Go here for additional help '
            'https://guides.platerecognizer.com/docs/stream/configuration#webhook-parameters.'
        )


def check_token(config):
    send_request(config)
    for camera in config.sections:
        if config[camera]['active']:
            send_request(config[camera])


def camera_spec():
    camera_global = dict(
        regions='force_list(default=list())',
        webhook_target='string(default="")',
        webhook_targets='force_list(default=list())',
        webhook_header='string(default="")',
        webhook_image='boolean(default=yes)',
        webhook_caching='boolean(default=yes)',
        webhook_image_type='option("vehicle", "original", default="vehicle")',
        webhook_request_timeout='float(default=30)',
        max_prediction_delay='float(default=6)',
        memory_decay='float(default=300)',
        image_format=
        'string(default="$(camera)_screenshots/%y-%m-%d/%H-%M-%S.%f.jpg")',
        sample='integer(default=2)',
        total='integer(default=-1)',
        mmc='boolean(default=no)',
        csv_file='string(default="")',
        jsonlines_file='string(default="")',
        region_config='option("normal", "strict", default="normal")',
        detection_rule='option("normal", "strict", default="normal")',
        detection_mode='option("plate", "vehicle", default="plate")',
        merge_buffer='integer(default=-1)',
    )

    camera = dict(
        url='string',
        active='boolean(default=yes)',
        # Overridable
        regions='force_list(default=None)',
        webhook_target='string(default=None)',
        webhook_targets='force_list(default=None)',
        webhook_header='string(default=None)',
        webhook_image='boolean(default=None)',
        webhook_caching='boolean(default=None)',
        webhook_image_type='option("vehicle", "original", default=None)',
        webhook_request_timeout='float(default=None)',
        max_prediction_delay='float(default=None)',
        memory_decay='float(default=None)',
        image_format='string(default=None)',
        sample='integer(default=None)',
        total='integer(default=None)',
        mmc='boolean(default=None)',
        csv_file='string(default=None)',
        jsonlines_file='string(default=None)',
        region_config='option("normal", "strict", default=None)',
        detection_rule='option("normal", "strict", default=None)',
        detection_mode='option("plate", "vehicle", default=None)',
        merge_buffer='integer(default=None)',
    )
    assert set(camera_global.keys()) <= set(camera.keys())
    return dict(__many__=camera, **camera_global)


def base_config(config_path: Path, config=None):

    spec = ConfigObj()
    spec['timezone'] = 'string(default="UTC")'
    spec['version'] = 'integer(default=2)'
    spec['cameras'] = camera_spec()
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
        return None, str(e)
    result = config.validate(Validator(), preserve_errors=True)
    errors = flatten_errors(config, result)
    if errors:
        error_message = '[STR0021] The config.ini file does not seem to be formatted correctly.  \n [Error details] \n'
        for section_list, key, error in errors:
            if error is False:
                error = 'key %s is missing.' % key
            elif key is not None:
                section_list.append(key)
            section_string = '/'.join(section_list)
            logging.error('%s: %s', section_string, error)
            error = f'{section_string}, param: {key}, message: {error}'
            error_message += '\n%s' % error
        return None, error_message + '\n Go here for additional help https://guides.platerecognizer.com/docs/stream/configuration'
    try:
        check_token(config['cameras'])
    except Exception as e:
        return None, str(e)
    return config, None
