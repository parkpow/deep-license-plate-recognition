import argparse
import os
import platform
import subprocess
import sys
import webbrowser
from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen  # type: ignore
    from urllib2 import URLError  # type: ignore

BASE_CONFIG = """#List of TZ names on https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
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

  image_format = $(camera)_screenshots/%y-%m-%d/%H-%M-%S.%f.jpg

  [[camera-1]]
    active = yes
    url = rtsp://192.168.0.108:8080/video/h264
    name = Camera One

    # Output methods. Uncomment line to enable.
    # - Save to CSV. The corresponding frame is stored as an image in the same directory.
    # - Send to Webhook. The recognition data and vehicle image are encoded in
    # multipart/form-data and sent to webhook_target.
    csv_file = camera-1.csv
    # webhook_target = http://webhook.site/
    # webhook_image = yes"""


def get_os():
    os_system = platform.system()
    if os_system == 'Windows':
        return 'Windows'
    elif os_system == 'Linux':
        return 'Linux'
    elif os_system == 'Darwin':
        return 'Mac OS'
    return os_system


def get_docker_link():
    docker_links = {
        'Windows': 'https://platerecognizer.com/help/docker/#install-SDK',
        'Linux': 'https://docs.docker.com/install/',
        'Mac OS':
        'https://hub.docker.com/editions/community/docker-ce-desktop-mac/'
    }
    return docker_links.get(get_os())


def verify_docker_install():
    try:
        subprocess.check_output("docker info".split(), stderr=-1)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def get_container_id(image):
    cmd = 'docker ps -q --filter ancestor={}'.format(image)
    output = subprocess.check_output(cmd.split())
    return output.decode()


def stop_container(image):
    container_id = get_container_id(image)
    if container_id:
        cmd = 'docker stop {}'.format(container_id)
        os.system(cmd)
    return container_id


def get_home(product='stream'):
    return str(Path.home() / product)


def get_image(image):
    images = subprocess.check_output(
        ['docker', 'images', '--format', '"{{.Repository}}"',
         image]).decode().split('\n')
    return images[0].replace('"', '')


def pull_docker(image):
    if get_container_id(image):
        stop_container(image)
    pull_cmd = f'docker pull {image}'
    os.system(pull_cmd)


def read_config(home):
    try:
        config = Path.joinpath(Path(home), 'config.ini')
        conf = ''
        f = open(config, 'r')
        for line in f:
            conf += line
        f.close()
        return conf
    except IOError:  # file not found
        return BASE_CONFIG


def write_config(home, config):
    try:
        path = Path.joinpath(Path(home), 'config.ini')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w+') as conf:
            for line in config:
                conf.write(line)
        return True
    except Exception:
        return False


def verify_token(token, license_key, get_license=True, product='stream'):
    path = 'stream/license' if product == 'stream' else 'sdk-webhooks'
    try:
        req = Request('https://app.platerecognizer.com/v1/{}/{}/'.format(
            path, license_key))
        req.add_header('Authorization', 'Token {}'.format(token))
        urlopen(req).read()
        return True, None
    except URLError as e:
        if '404' in str(e) and get_license:
            return False, 'The License Key cannot be found. Please try again.'
        elif str(403) in str(e):
            return False, 'The API Token cannot be found. Please try again.'
        else:
            return True, None


def is_valid_port(port):
    try:
        return 8000 <= int(port) <= 8999
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


DOCKER_LINK = get_docker_link()
SHARE_LINK = 'https://docs.google.com/document/d/1vLwyx4gQvv3gF_kQUvB5sLHoY0IlxV5b3gYUqR2wN1U/edit#heading=h.a7ccio5yriih'
STREAM_PLAN_LINK = 'https://app.platerecognizer.com/accounts/plan/#stream/?utm_source=installer&utm_medium=app'
SDK_PLAN_LINK = 'https://app.platerecognizer.com/accounts/plan/#sdk/?utm_source=installer&utm_medium=app'
STREAM_DOCS_LINK = 'https://docs.google.com/document/d/1vLwyx4gQvv3gF_kQUvB5sLHoY0IlxV5b3gYUqR2wN1U/edit#heading=h.u40inl8klrvj'
STREAM_IMAGE = 'platerecognizer/alpr-stream'
SDK_IMAGE = 'platerecognizer/alpr'
STREAM = 'stream'
SNAPSHOT = 'snapshot'
NONE = {'display': 'none'}
BLOCK = {'display': 'block'}
FLEX = {'display': 'flex'}
WIDTH = '91.5%'
DISPLAY_CARD = {'display': 'block', 'width': WIDTH}

DOCKER_INFO = [
    "Do you have Docker? If so, please run it now. "
    "If not, then please go here to install Docker on your machine: ",
    html.A(DOCKER_LINK, href=DOCKER_LINK, target='_blank')
]
if get_os() == 'Windows':
    DOCKER_INFO += [
        ". Make sure to check the box (next to C) for ",
        html.A('Resource File Sharing', href=SHARE_LINK, target='_blank'),
        " and the click “Apply & Restart”."
    ]


def get_os_label(product):
    return dbc.FormGroup([
        dbc.Label('Host OS', html_for=f'input-os-{product}', width=7),
        dbc.Label(get_os(), id=f'input-os-{product}', width=4),
    ],
                         row=True)


def get_refresh(product):
    return dbc.FormGroup([
        dbc.Label(DOCKER_INFO, html_for=f'refresh-docker-{product}', width=7),
        dcc.Loading(type='circle',
                    children=html.Div(id=f'loading-refresh-{product}')),
        dbc.Col(dbc.Button(
            'Refresh', color='secondary', id=f'refresh-docker-{product}'),
                width=4),
    ],
                         row=True,
                         style=NONE,
                         id=f'refresh-{product}')


def get_update(product):
    return dbc.FormGroup([
        dbc.Label(
            'Docker image found on your system, you may update or uninstall it:',
            html_for=f'update-image-{product}',
            width=7),
        dcc.Loading(type='circle',
                    children=html.Div(id=f'loading-update-{product}')),
        dcc.Loading(type='circle',
                    children=html.Div(id=f'loading-uninstall-{product}')),
        dbc.Col([
            dbc.Button(
                'Update', color='secondary', id=f'update-image-{product}'),
            html.Span(' Updated',
                      id=f'span-update-{product}',
                      className='align-middle'),
            dbc.Button('Uninstall',
                       color='danger',
                       id=f'uninstall-image-{product}',
                       style={'float': 'right'}),
            html.Span('',
                      id=f'span-uninstall-{product}',
                      className='align-middle',
                      style={
                          'float': 'right',
                          'color': 'red'
                      }),
            dbc.Modal(
                [
                    dbc.ModalHeader('Uninstall'),
                    dbc.ModalBody(
                        'Are you sure you want to uninstall an image?'),
                    dbc.ModalFooter([
                        dbc.Button(
                            'OK', color='danger', id=f'ok-uninstall-{product}'),
                        dbc.Button('Cancel', id=f'cancel-uninstall-{product}')
                    ]),
                ],
                id=f'modal-uninstall-{product}',
                centered=True,
            ),
        ],
                width=4),
    ],
                         row=True,
                         style=NONE,
                         id=f'update-{product}')


def get_token(product):
    link = STREAM_PLAN_LINK if product == 'stream' else SDK_PLAN_LINK
    return dbc.FormGroup([
        dbc.Label([
            'Please enter your Plate Recognizer ',
            html.A('API Token', href=link, target='_blank'), ':'
        ],
                  html_for=f'input-token-{product}',
                  width=7),
        dbc.Col(
            dbc.Input(type='text',
                      id=f'input-token-{product}',
                      placeholder='Token',
                      persistence=True),
            width=4,
        ),
    ],
                         row=True)


def get_license_key(product):
    link = STREAM_PLAN_LINK if product == 'stream' else SDK_PLAN_LINK
    return dbc.FormGroup([
        dbc.Label([
            'Please enter your ',
            html.A(f'{product.capitalize()} License Key',
                   href=link,
                   target='_blank'), ':'
        ],
                  html_for=f'input-key-{product}',
                  width=7),
        dbc.Col(
            dbc.Input(type='text',
                      id=f'input-key-{product}',
                      placeholder='License Key',
                      persistence=True),
            width=4,
        ),
    ],
                         row=True)


def get_directory(product):
    return dbc.FormGroup([
        dbc.Label(
            f'Path to your {product.capitalize()} installation directory:',
            html_for=f'input-home-{product}',
            width=7),
        dbc.Col(dbc.Input(value=get_home(),
                          type='text',
                          id=f'input-home-{product}',
                          placeholder='Path to directory',
                          persistence=True),
                width=4),
    ],
                         className='mb-2',
                         row=True)


def get_boot(product):
    return dbc.FormGroup([
        dbc.Label([
            f'Do you want {product.capitalize()} to automatically start on system startup?'
        ],
                  html_for=f'check-boot-{product}',
                  width=7),
        dbc.Col(dbc.Checkbox(id=f'check-boot-{product}',
                             className='align-bottom'),
                width=4)
    ],
                         row=True)


def get_port(product):
    return dbc.FormGroup([
        dbc.Label(['Set the container port (default is 8080):'],
                  html_for=f'input-port-{product}',
                  width=7),
        dbc.Col(
            dbc.Input(type='text',
                      id=f'input-port-{product}',
                      value='8080',
                      placeholder='Port',
                      persistence=True),
            width=4,
        ),
    ],
                         row=True)


def get_hardware_dropdown(product):
    return dbc.FormGroup([
        dbc.Label('What is the hardware of this machine?',
                  html_for=f'dropdown-hardware-{product}',
                  width=7),
        dbc.Col(
            dcc.Dropdown(options=[
                {
                    'label': 'Intel CPU',
                    'value': 'sdk'
                },
                {
                    'label': 'Raspberry',
                    'value': 'raspberry-pi'
                },
                {
                    'label': 'GPU (Nvidia Only)',
                    'value': 'gpu'
                },
                {
                    'label': 'Jetson Nano',
                    'value': 'jetson'
                },
            ],
                         value='sdk',
                         clearable=False,
                         id=f'dropdown-hardware-{product}',
                         style={'borderRadius': '0'},
                         persistence=True),
            width=4,
        ),
    ],
                         className='mb-2',
                         row=True)


def get_config_label(product):
    return html.P([
        'Edit your Stream configuration file. See the ',
        html.A('documentation', href=STREAM_DOCS_LINK, target='_blank'),
        ' for details.'
    ])


def get_config_body(product):
    return dbc.Textarea(bs_size='sm',
                        id=f'area-config-{product}',
                        style={
                            'width': WIDTH,
                            'height': '300px'
                        })


def get_status(product):
    return html.P(children='',
                  style={'color': 'red'},
                  className='mb-0',
                  id=f'p-status-{product}')


def get_success_card(product):
    result = f'You can now start {product.capitalize()}. Open a terminal and type the command below. You can save this command for future use.'
    if product == SNAPSHOT:
        result += ' To use the SDK endpoint call: curl -F "upload=@my_file.jpg" http://localhost:8080/v1/plate-reader/'
    return dbc.CardBody([
        html.H5(result, className='card-title'),
        html.P(className='card-text', id=f'command-{product}'),
        html.Button('copy to clipboard',
                    id=f'copy-{product}',
                    **{'data-clipboard-target': f'#command-{product}'},
                    className='btn btn-sm btn-warning',
                    style={'borderRadius': '15px'}),
        html.Span(id=f'copy-status-{product}',
                  className='align-middle ml-2',
                  style={
                      'fontSize': '13px',
                      'color': 'green'
                  })
    ])


def get_continue(product):
    return dbc.Button('Continue',
                      color='primary',
                      id=f'button-submit-{product}',
                      className='my-3')


def get_loading_submit(product):
    return dcc.Loading(type='circle',
                       children=html.Div(id=f'loading-submit-{product}'))


def get_image_name(hardware):
    if hardware == 'raspberry-pi':
        return SDK_IMAGE + '-raspberry-pi'
    elif hardware == 'gpu':
        return SDK_IMAGE + '-gpu'
    elif hardware == 'jetson':
        return SDK_IMAGE + '-jetson'
    else:
        return SDK_IMAGE


def get_confirm(product):
    return dcc.ConfirmDialogProvider(
        children=html.Button('Click Me',),
        id='danger-danger-provider',
        message='Danger danger! Are you sure you want to continue?'),


app = dash.Dash(
    __name__,
    title='Plate Recognizer Installer',
    assets_folder=resource_path('assets'),
    external_stylesheets=[dbc.themes.YETI],
    external_scripts=[
        'https://cdn.jsdelivr.net/npm/clipboard@2.0.6/dist/clipboard.min.js'
    ])

app.layout = dbc.Container([
    html.H2(children='Plate Recognizer Installer',
            className='text-center my-3'),
    dbc.Tabs([
        dbc.Tab([
            dbc.Form([
                get_os_label(STREAM),
                get_refresh(STREAM),
                get_update(STREAM),
            ],
                     className='mt-2'),
            dbc.Form([
                get_token(STREAM),
                get_license_key(STREAM),
                get_directory(STREAM),
                get_boot(STREAM),
            ],
                     style=NONE,
                     id=f'form-{STREAM}'),
            html.Div([
                get_config_label(STREAM),
                get_config_body(STREAM),
                get_status(STREAM),
                dbc.Card([get_success_card(STREAM)],
                         id=f'card-{STREAM}',
                         className='mt-3',
                         style=NONE),
                get_loading_submit(STREAM),
                get_continue(STREAM),
            ],
                     id=f'footer-{STREAM}',
                     style=NONE),
        ],
                label=STREAM.capitalize(),
                tab_id=STREAM,
                className='offset-md-1'),
        dbc.Tab([
            dbc.Form([
                get_os_label(SNAPSHOT),
                get_refresh(SNAPSHOT),
                get_update(SNAPSHOT),
            ],
                     className='mt-2'),
            dbc.Form([
                get_token(SNAPSHOT),
                get_license_key(SNAPSHOT),
                get_boot(SNAPSHOT),
                get_port(SNAPSHOT),
                get_hardware_dropdown(SNAPSHOT)
            ],
                     style=NONE,
                     id=f'form-{SNAPSHOT}'),
            html.Div([
                get_status(SNAPSHOT),
                dbc.Card([get_success_card(SNAPSHOT)],
                         id=f'card-{SNAPSHOT}',
                         className='mt-3',
                         style=NONE),
                get_loading_submit(SNAPSHOT),
                get_continue(SNAPSHOT),
            ],
                     id=f'footer-{SNAPSHOT}',
                     style=NONE),
        ],
                label=SNAPSHOT.capitalize(),
                tab_id=SNAPSHOT,
                className='offset-md-1')
    ],
             id='tabs',
             active_tab=STREAM,
             style={'width': '84%'},
             className='offset-md-1 justify-content-center'),
])


@app.callback([
    Output('refresh-stream', 'style'),
    Output('update-stream', 'style'),
    Output('form-stream', 'style'),
    Output('footer-stream', 'style'),
    Output('loading-refresh-stream', 'children')
], [
    Input('refresh-docker-stream', 'n_clicks'),
])
def refresh_docker_stream(n_clicks):
    if verify_docker_install():
        if get_image(STREAM_IMAGE):
            return NONE, FLEX, BLOCK, BLOCK, None
        else:
            return NONE, NONE, BLOCK, BLOCK, None
    else:
        return FLEX, NONE, NONE, NONE, None


@app.callback([
    Output('refresh-snapshot', 'style'),
    Output('update-snapshot', 'style'),
    Output('form-snapshot', 'style'),
    Output('footer-snapshot', 'style'),
    Output('loading-refresh-snapshot', 'children')
], [
    Input('refresh-docker-snapshot', 'n_clicks'),
    Input('dropdown-hardware-snapshot', 'value')
])
def refresh_docker_snapshot(n_clicks, hardware):
    if verify_docker_install():
        if get_image(get_image_name(hardware)):
            return NONE, FLEX, BLOCK, BLOCK, None
        else:
            return NONE, NONE, BLOCK, BLOCK, None
    else:
        return FLEX, NONE, NONE, NONE, None


@app.callback([
    Output('update-image-stream', 'disabled'),
    Output('span-update-stream', 'style'),
    Output('loading-update-stream', 'children')
], [Input('update-image-stream', 'n_clicks'),
    Input('tabs', 'active_tab')])
def update_image_stream(n_clicks, tab):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'update-image-stream.n_clicks':
        pull_docker(STREAM_IMAGE)
        return False, {'display': 'inline', 'color': 'green'}, None
    return False, NONE, None


@app.callback([
    Output('update-image-snapshot', 'disabled'),
    Output('span-update-snapshot', 'style'),
    Output('loading-update-snapshot', 'children')
], [
    Input('update-image-snapshot', 'n_clicks'),
    Input('tabs', 'active_tab'),
    Input('dropdown-hardware-snapshot', 'value')
])
def update_image_snapshot(n_clicks, tab, hardware):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'update-image-snapshot.n_clicks':
        pull_docker(get_image_name(hardware))
        return False, {'display': 'inline', 'color': 'green'}, None
    return False, NONE, None


@app.callback(
    Output('modal-uninstall-stream', 'is_open'),
    [
        Input('uninstall-image-stream', 'n_clicks'),
        Input('ok-uninstall-stream', 'n_clicks'),
        Input('cancel-uninstall-stream', 'n_clicks'),
    ],
    [State('modal-uninstall-stream', 'is_open')],
)
def toggle_modal_stream(n1, n2, n3, is_open):
    if n1 or n2 or n3:
        return not is_open
    return is_open


@app.callback(
    Output('modal-uninstall-snapshot', 'is_open'),
    [
        Input('uninstall-image-snapshot', 'n_clicks'),
        Input('ok-uninstall-snapshot', 'n_clicks'),
        Input('cancel-uninstall-snapshot', 'n_clicks'),
    ],
    [State('modal-uninstall-snapshot', 'is_open')],
)
def toggle_modal_snapshot(n1, n2, n3, is_open):
    if n1 or n2 or n3:
        return not is_open
    return is_open


@app.callback([
    Output('loading-uninstall-stream', 'children'),
    Output('span-uninstall-stream', 'children'),
], [
    Input('ok-uninstall-stream', 'n_clicks'),
    Input('update-image-stream', 'n_clicks'),
    State('input-token-stream', 'value'),
    State('input-key-stream', 'value'),
])
def uninstall_stream(n_clicks, update, token, key):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'update-image-stream.n_clicks':
        return [None, '']
    if dash.callback_context.triggered[0][
            'prop_id'] == 'ok-uninstall-stream.n_clicks':
        if not get_image(STREAM_IMAGE):
            return [None, 'Image already uninstalled.']
        stop_container(STREAM_IMAGE)
        container_id = get_container_id(STREAM_IMAGE)
        if container_id:
            cmd = f'docker container rm {container_id}'
            os.system(cmd)
        cmd = f'docker rmi "{STREAM_IMAGE}" -f'
        os.system(cmd)
        cmd = 'docker image prune -f'
        os.system(cmd)
        return [None, 'Image successfully uninstalled.']
    raise PreventUpdate


@app.callback([
    Output('loading-uninstall-snapshot', 'children'),
    Output('span-uninstall-snapshot', 'children'),
], [
    Input('ok-uninstall-snapshot', 'n_clicks'),
    Input('update-image-snapshot', 'n_clicks'),
    Input('dropdown-hardware-snapshot', 'value'),
    State('input-token-snapshot', 'value'),
    State('input-key-snapshot', 'value'),
    State('dropdown-hardware-snapshot', 'value')
])
def uninstall_snapshot(n_clicks, update, switch, token, key, hardware):
    if dash.callback_context.triggered[0]['prop_id'] in [
            'update-image-snapshot.n_clicks', 'dropdown-hardware-snapshot.value'
    ]:
        return [None, '']
    if dash.callback_context.triggered[0][
            'prop_id'] == 'ok-uninstall-snapshot.n_clicks':
        if not get_image(get_image_name(hardware)):
            return [None, 'Image already uninstalled.']
        verification = verify_token(token, key, product=SNAPSHOT)
        if verification[0]:
            stop_container(get_image_name(hardware))
            cmd = f'docker run --rm -t -v license:/license -e TOKEN={token} -e LICENSE_KEY={key} -e UNINSTALL=1 {get_image_name(hardware)}'
            os.system(cmd)
            container_id = get_container_id(get_image_name(hardware))
            if container_id:
                cmd = f'docker container rm {container_id}'
                os.system(cmd)
            cmd = f'docker rmi "{get_image_name(hardware)}" -f'
            os.system(cmd)
            cmd = 'docker image prune -f'
            os.system(cmd)
            return [None, 'Image successfully uninstalled.']
        else:
            return [None, verification[1]]
    raise PreventUpdate


@app.callback(Output('area-config-stream', 'value'),
              [Input('input-home-stream', 'value')])
def change_path(home):
    return read_config(home)


@app.callback([
    Output('p-status-stream', 'children'),
    Output('card-stream', 'style'),
    Output('command-stream', 'children'),
    Output('loading-submit-stream', 'children')
], [
    Input('area-config-stream', 'value'),
    Input('button-submit-stream', 'n_clicks'),
    Input('input-token-stream', 'value'),
    Input('input-key-stream', 'value'),
    Input('input-home-stream', 'value'),
    Input('check-boot-stream', 'checked'),
])
def submit_stream(config, n_clicks, token, key, home, boot):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'button-submit-stream.n_clicks':
        is_valid, error = verify_token(token, key, product='stream')
        if is_valid:
            if not write_config(home, config):
                return f'The Installation Directory is not valid. Please enter a valid folder, such as {get_home()}', NONE, '', None
            user_info = ''
            nvidia = ''
            image_tag = ''
            autoboot = '--rm'
            if get_os() != 'Windows':
                user_info = '--user `id -u`:`id -g`'
            if os.path.exists('/etc/nv_tegra_release'):
                nvidia = '--runtime nvidia --privileged --group-add video'
                image_tag = ':jetson'
            if boot:
                autoboot = '--restart unless-stopped'
            if not get_image(STREAM_IMAGE):
                pull_docker(STREAM_IMAGE)
            command = f'docker run {autoboot} -t ' \
                      f'{nvidia} --name stream ' \
                      f'-v {home}:/user-data ' \
                      f'{user_info} ' \
                      f'-e LICENSE_KEY={key} ' \
                      f'-e TOKEN={token} ' \
                      f'{STREAM_IMAGE}{image_tag}'
            return '', DISPLAY_CARD, command, None
        else:
            return error, NONE, '', None
    else:
        return '', NONE, '', None


@app.callback([
    Output('p-status-snapshot', 'children'),
    Output('card-snapshot', 'style'),
    Output('command-snapshot', 'children'),
    Output('loading-submit-snapshot', 'children')
], [
    Input('button-submit-snapshot', 'n_clicks'),
    Input('input-token-snapshot', 'value'),
    Input('input-key-snapshot', 'value'),
    Input('check-boot-snapshot', 'checked'),
    Input('input-port-snapshot', 'value'),
    Input('dropdown-hardware-snapshot', 'value'),
])
def submit_snapshot(n_clicks, token, key, boot, port, hardware):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'button-submit-snapshot.n_clicks':
        is_valid, error = verify_token(token, key, product='snapshot')
        if is_valid:
            autoboot = '--restart unless-stopped' if boot else '--rm'
            if not is_valid_port(port):
                return 'Wrong port', NONE, '', None
            if not get_image(get_image_name(hardware)):
                pull_docker(get_image_name(hardware))
            docker_version = 'nvidia-docker' if 'jetson' in get_image_name(
                hardware) else 'docker'
            extra_args = '--runtime nvidia' if any(h in get_image_name(hardware)
                                                   for h in ('gpu',
                                                             'jetson')) else ''
            command = f'{docker_version} run {autoboot} ' \
                      f'-t {extra_args} ' \
                      f'-p {port}:8080 ' \
                      f'-v license:/license ' \
                      f'-e LICENSE_KEY={key} ' \
                      f'-e TOKEN={token} ' \
                      f'{get_image_name(hardware)}'
            return '', DISPLAY_CARD, command, None
        else:
            return error, NONE, '', None
    else:
        return '', NONE, '', None


@app.callback(Output('copy-status-stream', 'children'), [
    Input('copy-stream', 'n_clicks'),
    Input('button-submit-stream', 'n_clicks'),
])
def copy_to_clipboard_stream(n_clicks, n_clicks_submit):
    if dash.callback_context.triggered[0]['prop_id'] == 'copy-stream.n_clicks':
        return 'Item copied to clipboard.'
    else:
        return ''


@app.callback(Output('copy-status-snapshot', 'children'), [
    Input('copy-snapshot', 'n_clicks'),
    Input('button-submit-snapshot', 'n_clicks'),
])
def copy_to_clipboard_snapshot(n_clicks, n_clicks_submit):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'copy-snapshot.n_clicks':
        return 'Item copied to clipboard.'
    else:
        return ''


def parse_arguments():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--debug', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    print('''
############################################
# Thank you for choosing Plate Recognizer! #
############################################

- To continue open http://127.0.0.1:8050/ in your web browser.

- When you are done with the installation, you can close this window.

############################################
''')
    if args.debug:
        app.run_server(debug=True)
    else:
        webbrowser.open('http://127.0.0.1:8050/')
        app.run_server(debug=False, dev_tools_silence_routes_logging=True)
