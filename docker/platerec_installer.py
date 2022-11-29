import argparse
import base64
import logging
import os
import re
import sys
import time
import webbrowser
import installer_helpers as helpers

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

SHARE_LINK = 'https://guides.platerecognizer.com/docs/stream/manual-install#step-2'
STREAM_PLAN_LINK = 'https://app.platerecognizer.com/accounts/plan/#stream/?utm_source=installer&utm_medium=app'
SDK_PLAN_LINK = 'https://app.platerecognizer.com/accounts/plan/#sdk/?utm_source=installer&utm_medium=app'
STREAM_DOCS_LINK = 'https://guides.platerecognizer.com/docs/stream/configuration'
STREAM_IMAGE = 'platerecognizer/alpr-stream'
SDK_IMAGE = 'platerecognizer/alpr'
STREAM = 'stream'
SNAPSHOT = 'snapshot'
USER_DATA = '/user-data/'
NONE = {'display': 'none'}
BLOCK = {'display': 'block'}
FLEX = {'display': 'flex'}
WIDTH = '91.5%'
DISPLAY_CARD = {'display': 'block', 'width': WIDTH}
CONSOLE_WELCOME = '''
############################################
# Thank you for choosing Plate Recognizer! #
############################################

- To continue open http://localhost:8050/ in your web browser. If your browser is
on a separate device, replace "localhost" by the host's IP.

- When you are done with the installation, you can close this window.

############################################'''


def get_splash_screen():
    return html.Div([
        html.Div([
            html.H2('Please choose a product:', className='splash-header'),
            dbc.Button('Stream', size='lg', id='button-choose-stream'),
            dbc.Button('Snapshot',
                       size='lg',
                       id='button-choose-snapshot',
                       className='ml-3'),
        ],
                 className='splash')
    ],
                    className='background')


def get_refresh(product):
    docker_links = {
        'Windows': 'https://platerecognizer.com/docker/#install-SDK',
        'Linux': 'https://docs.docker.com/install/',
        'Mac OS':
        'https://hub.docker.com/editions/community/docker-ce-desktop-mac/'
    }
    docker_link = docker_links.get(helpers.get_os())
    docker_info = [
        "Do you have Docker? If so, please run it now. "
        "If not, then please go here to install Docker on your machine: ",
        html.A(docker_link, href=docker_link, target='_blank')
    ]
    permission_error_info = [
        "Got a 'permission denied error' while trying to connect to the Docker daemon. "
        "Does the user running the installer able to execute Docker commands?"
    ]
    if helpers.get_os() == 'Windows':
        docker_info += [
            ". If using the legacy Hyper-V backend and not WSL2, "
            "Make sure to check the box (next to C) for ",
            html.A('Resource File Sharing', href=SHARE_LINK, target='_blank'),
            " and the click “Apply & Restart”."
        ]
    return dbc.FormGroup([
        dbc.Label(docker_info,
                  id=f'info-docker-{product}',
                  html_for=f'refresh-docker-{product}',
                  style=BLOCK,
                  width=7),
        dbc.Label(permission_error_info,
                  id=f'permissions-docker-{product}',
                  html_for=f'refresh-docker-{product}',
                  style=NONE,
                  width=7),
        dcc.Loading(type='circle',
                    children=html.Div(id=f'loading-refresh-{product}')),
        dbc.Col(dbc.Button(
            'Refresh', color='secondary', id=f'refresh-docker-{product}'),
                width=4),
    ],
                         row=True,
                         style=BLOCK,
                         id=f'refresh-{product}')


def get_update(product):
    return dbc.FormGroup([
        dbc.Col([
            dbc.Button(
                'Update', color='secondary', id=f'update-image-{product}'),
            html.Span('Updated',
                      id=f'span-update-{product}',
                      className='align-middle'),
        ],
                width=1),
        dcc.Loading(type='circle',
                    children=html.Div(id=f'loading-update-{product}')),
        dbc.Label('Update the Docker image.',
                  html_for=f'update-image-{product}',
                  width=11),
    ],
                         row=True,
                         style=NONE,
                         id=f'update-{product}')


def get_uninstall(product):
    return dbc.FormGroup([
        dbc.Col([
            dbc.Button(
                'Uninstall', color='danger', id=f'uninstall-image-{product}'),
            html.Span('',
                      id=f'span-uninstall-{product}',
                      className='align-middle',
                      style={'color': 'red'}),
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
                width=1),
        dcc.Loading(type='circle',
                    children=html.Div(id=f'loading-uninstall-{product}')),
        dbc.Label(
            'Remove the Docker image and mark the product as uninstalled.',
            html_for=f'uninstall-image-{product}',
            width=11),
    ],
                         row=True,
                         style=NONE,
                         id=f'uninstall-{product}')


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
        dbc.Col(dbc.Input(value=helpers.get_home(),
                          type='text',
                          id=f'input-home-{product}',
                          placeholder='Path to directory',
                          persistence=True),
                width=4),
    ],
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
        dbc.Label('Docker image to use:',
                  html_for=f'dropdown-hardware-{product}',
                  width=7),
        dbc.Col(
            dcc.Dropdown(options=[
                {
                    'label': 'Intel CPU',
                    'value': 'platerecognizer/alpr:latest'
                },
                {
                    'label': 'Raspberry',
                    'value': 'platerecognizer/alpr-raspberry-pi:latest'
                },
                {
                    'label': 'GPU (Nvidia Only)',
                    'value': 'platerecognizer/alpr-gpu:latest'
                },
                {
                    'label': 'Jetson Nano',
                    'value': 'platerecognizer/alpr-jetson:latest'
                },
                {
                    'label': 'ZCU104',
                    'value': 'platerecognizer/alpr-zcu104:latest'
                },
                {
                    'label': 'Thailand',
                    'value': 'platerecognizer/alpr:thailand'
                },
            ],
                         value='platerecognizer/alpr:latest',
                         clearable=False,
                         id=f'dropdown-hardware-{product}',
                         style={'borderRadius': '0'},
                         persistence=True),
            width=4,
        ),
    ],
                         className='mb-3',
                         row=True)


def get_video_checkbox(product):
    return dbc.FormGroup([
        dbc.Label([f'Use {product.capitalize()} on a local video file.'],
                  html_for=f'check-video-{product}',
                  width=7),
        dbc.Col(dbc.Checkbox(id=f'check-video-{product}',
                             className='align-bottom',
                             persistence=True),
                width=4)
    ],
                         row=True)


def get_video_picker(product):
    return dbc.FormGroup([
        dbc.Label([
            f'Select a video file. If it is not inside your {product.capitalize()} folder, we will copy it there. Big files (~400Mb) may slow down your system.'
        ],
                  html_for=f'pickup-video-{product}',
                  width=7),
        dcc.Loading(type='circle',
                    children=html.Div(id=f'loading-upload-{product}')),
        dbc.Col(
            [
                dcc.Upload([
                    dbc.Button('Upload File'),
                    html.Span(
                        '', id=f'span-videopath-{product}', className='ml-2')
                ],
                           id=f'pickup-video-{product}',
                           accept='video/*'),
            ],
            width=4,
        ),
    ],
                         id=f'pickup-{product}',
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
    sdk_endpoint = ''
    if product == SNAPSHOT:
        sdk_endpoint = [
            html.P(' To use the SDK endpoint call: ',
                   className='card-title mt-3 mb-0',
                   style={'display': 'inline-block'}),
            html.Code(
                ' curl -F "upload=@my_file.jpg" http://localhost:8080/v1/plate-reader/'
            )
        ]
    return dbc.CardBody([
        html.
        P(f'You can now start {product.capitalize()}. Open a terminal and type the command below. You can save this command for future use.',
          className='card-title'),
        html.Code(className='card-text d-block', id=f'command-{product}'),
        html.Div([
            html.Button('copy to clipboard',
                        id=f'copy-{product}',
                        **{'data-clipboard-target': f'#command-{product}'},
                        className='btn btn-sm btn-warning',
                        style={'borderRadius': '15px'}),
            html.Span(id=f'copy-status-{product}',
                      className='ml-2',
                      style={
                          'fontSize': '13px',
                          'color': 'green'
                      }),
        ],
                 className='mt-3'),
        html.P(sdk_endpoint, className='my-0')
    ])


def get_continue(product):
    return dbc.FormGroup([
        dbc.Col([
            dbc.Button('Show Docker Command',
                       color='primary',
                       id=f'button-submit-{product}'),
        ],
                width=1),
        dbc.Label('Confirm settings and show docker command.',
                  html_for=f'button-submit-{product}',
                  width=11),
    ],
                         row=True,
                         className='mt-3')


def get_loading_submit(product):
    return dcc.Loading(type='circle',
                       children=html.Div(id=f'loading-submit-{product}'))


def get_confirm(product):
    return dcc.ConfirmDialogProvider(
        children=html.Button('Click Me',),
        id='danger-danger-provider',
        message='Danger danger! Are you sure you want to continue?'),


############
# Dash App #
############

app = dash.Dash(
    __name__,
    title='Plate Recognizer Installer',
    assets_folder=helpers.resource_path('assets'),
    external_stylesheets=[dbc.themes.YETI],
    external_scripts=[
        'https://cdn.jsdelivr.net/npm/clipboard@2.0.6/dist/clipboard.min.js'
    ])

app.layout = dbc.Container([
    get_splash_screen(),
    html.H2(children='Plate Recognizer Installer',
            className='text-center my-3'),
    dbc.Tabs([
        dbc.Tab([
            dbc.Form([
                get_refresh(STREAM),
            ], className='mt-3'),
            dbc.Form([
                get_token(STREAM),
                get_license_key(STREAM),
                get_directory(STREAM),
                get_boot(STREAM),
                get_video_checkbox(STREAM),
                get_video_picker(STREAM),
            ],
                     style=NONE,
                     className='mt-3',
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
            ],
                     id=f'footer-{STREAM}',
                     className='mt-3',
                     style=NONE),
            dbc.Form([
                get_continue(STREAM),
                get_update(STREAM),
                get_uninstall(STREAM)
            ],
                     style=NONE,
                     id=f'form-update-{STREAM}'),
        ],
                label=STREAM.capitalize(),
                tab_id=STREAM,
                className='offset-md-1 stream-tab'),
        dbc.Tab([
            dbc.Form([
                get_refresh(SNAPSHOT),
            ], className='mt-3'),
            dbc.Form([
                get_token(SNAPSHOT),
                get_license_key(SNAPSHOT),
                get_boot(SNAPSHOT),
                get_port(SNAPSHOT),
                get_hardware_dropdown(SNAPSHOT),
            ],
                     style=NONE,
                     className='mt-3',
                     id=f'form-{SNAPSHOT}'),
            html.Div([
                get_status(SNAPSHOT),
                dbc.Card([get_success_card(SNAPSHOT)],
                         id=f'card-{SNAPSHOT}',
                         className='mt-3',
                         style=NONE),
                get_loading_submit(SNAPSHOT),
            ],
                     id=f'footer-{SNAPSHOT}',
                     className='mt-3',
                     style=NONE),
            dbc.Form([
                get_continue(SNAPSHOT),
                get_update(SNAPSHOT),
                get_uninstall(SNAPSHOT)
            ],
                     style=NONE,
                     id=f'form-update-{SNAPSHOT}'),
        ],
                label=SNAPSHOT.capitalize(),
                tab_id=SNAPSHOT,
                className='offset-md-1 snapshot-tab')
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
    Output('form-update-stream', 'style'),
    Output('footer-stream', 'style'),
    Output('loading-refresh-stream', 'children'),
    Output('info-docker-stream', 'style'),
    Output('permissions-docker-stream', 'style')
], [
    Input('refresh-docker-stream', 'n_clicks'),
    Input('ok-uninstall-stream', 'n_clicks')
])
def refresh_docker_stream(n_clicks, uninstall):
    try:
        docker_is_ok = helpers.verify_docker_install()
    except helpers.DockerPermissionError:
        return FLEX, NONE, NONE, NONE, NONE, None, NONE, BLOCK
    if docker_is_ok:
        if dash.callback_context.triggered[0][
                'prop_id'] == 'ok-uninstall-stream.n_clicks':
            time.sleep(2)
            return NONE, NONE, BLOCK, BLOCK, BLOCK, None, BLOCK, NONE
        if helpers.get_image(STREAM_IMAGE):
            return NONE, FLEX, BLOCK, BLOCK, BLOCK, None, BLOCK, NONE
        else:
            return NONE, NONE, BLOCK, BLOCK, BLOCK, None, BLOCK, NONE
    else:
        return FLEX, NONE, NONE, NONE, NONE, None, BLOCK, NONE


@app.callback([
    Output('refresh-snapshot', 'style'),
    Output('update-snapshot', 'style'),
    Output('form-snapshot', 'style'),
    Output('form-update-snapshot', 'style'),
    Output('footer-snapshot', 'style'),
    Output('loading-refresh-snapshot', 'children'),
    Output('info-docker-snapshot', 'style'),
    Output('permissions-docker-snapshot', 'style')
], [
    Input('refresh-docker-snapshot', 'n_clicks'),
    Input('dropdown-hardware-snapshot', 'value'),
    Input('ok-uninstall-snapshot', 'n_clicks')
])
def refresh_docker_snapshot(n_clicks, hardware, uninstall):
    try:
        docker_is_ok = helpers.verify_docker_install()
    except helpers.DockerPermissionError:
        return FLEX, NONE, NONE, NONE, NONE, None, NONE, BLOCK
    if docker_is_ok:
        if dash.callback_context.triggered[0][
                'prop_id'] == 'ok-uninstall-snapshot.n_clicks':
            time.sleep(2)
            return NONE, NONE, BLOCK, BLOCK, BLOCK, None, BLOCK, NONE
        if helpers.get_image(hardware):
            return NONE, FLEX, BLOCK, BLOCK, BLOCK, None, BLOCK, NONE
        else:
            return NONE, NONE, BLOCK, BLOCK, BLOCK, None, BLOCK, NONE
    else:
        return FLEX, NONE, NONE, NONE, NONE, None, BLOCK, NONE


@app.callback([
    Output('pickup-stream', 'style'),
], [
    Input('check-video-stream', 'checked'),
])
def select_video(checked):
    if checked:
        return [FLEX]
    else:
        return [NONE]


@app.callback([
    Output('span-videopath-stream', 'children'),
    Output('loading-upload-stream', 'children')
], [
    Input('pickup-video-stream', 'contents'),
    State('pickup-video-stream', 'filename'),
    State('input-home-stream', 'value')
])
def set_videopath(content, name, path):
    if content and name and path:
        return [name, None]
    elif name and path:
        return ['File error', None]
    else:
        raise PreventUpdate


@app.callback([
    Output('update-image-stream', 'disabled'),
    Output('span-update-stream', 'style'),
    Output('loading-update-stream', 'children')
], [Input('update-image-stream', 'n_clicks'),
    Input('tabs', 'active_tab')])
def update_image_stream(n_clicks, tab):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'update-image-stream.n_clicks':
        helpers.pull_docker(STREAM_IMAGE)
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
        helpers.pull_docker(hardware)
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
    Output('uninstall-stream', 'style'),
], [Input('ok-uninstall-stream', 'n_clicks')])
def uninstall_button_stream(n_clicks):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'ok-uninstall-stream.n_clicks':
        time.sleep(2)
        return [NONE]
    if not helpers.verify_docker_install():
        return [NONE]
    if helpers.get_image(STREAM_IMAGE):
        return [FLEX]
    else:
        return [NONE]


@app.callback([
    Output('uninstall-snapshot', 'style'),
], [
    Input('ok-uninstall-snapshot', 'n_clicks'),
    Input('dropdown-hardware-snapshot', 'value'),
])
def uninstall_button_snapshot(n_clicks, hardware):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'ok-uninstall-snapshot.n_clicks':
        time.sleep(2)
        return [NONE]
    if not helpers.verify_docker_install():
        return [NONE]
    if helpers.get_image(hardware):
        return [FLEX]
    else:
        return [NONE]


@app.callback([
    Output('loading-uninstall-stream', 'children'),
    Output('span-uninstall-stream', 'children'),
], [
    Input('ok-uninstall-stream', 'n_clicks'),
    State('input-token-stream', 'value'),
    State('input-key-stream', 'value'),
])
def uninstall_stream(n_clicks, token, key):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'ok-uninstall-stream.n_clicks':
        if not helpers.get_image(STREAM_IMAGE):
            return [None, 'Image already uninstalled.']
        helpers.stop_container(STREAM_IMAGE)
        return helpers.uninstall_docker_image(STREAM_IMAGE)
    raise PreventUpdate


@app.callback([
    Output('loading-uninstall-snapshot', 'children'),
    Output('span-uninstall-snapshot', 'children'),
], [
    Input('ok-uninstall-snapshot', 'n_clicks'),
    Input('dropdown-hardware-snapshot', 'value'),
    State('input-token-snapshot', 'value'),
    State('input-key-snapshot', 'value')
])
def uninstall_snapshot(n_clicks, hardware, token, key):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'dropdown-hardware-snapshot.value':
        return [None, '']
    if dash.callback_context.triggered[0][
            'prop_id'] == 'ok-uninstall-snapshot.n_clicks':
        if not helpers.get_image(hardware):
            return [None, 'Image already uninstalled.']
        verification = helpers.verify_token(token, key, product=SNAPSHOT)
        if verification[0]:
            helpers.stop_container(hardware)
            cmd = f'docker run --rm -t -v license:/license -e TOKEN={token} -e LICENSE_KEY={key} -e UNINSTALL=1 {hardware}'
            os.system(cmd)
            return helpers.uninstall_docker_image(hardware)
        else:
            return [None, verification[1]]
    raise PreventUpdate


@app.callback(Output('area-config-stream', 'value'), [
    Input('input-home-stream', 'value'),
    Input('pickup-video-stream', 'filename'),
    State('check-video-stream', 'checked'),
])
def change_path(home, videofile, videocheck):
    config = helpers.read_config(home)
    if videofile and videocheck:  # replace url with a path to video
        url = re.search('url = (.*)\n', config).group(1)
        config = re.sub(url, f'{USER_DATA}{videofile}', config)
    return config


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
    State('pickup-video-stream', 'contents'),
    State('pickup-video-stream', 'filename'),
    State('check-video-stream', 'checked'),
])
def submit_stream(config, n_clicks, token, key, home, boot, videocontent,
                  videofile, videocheck):
    if dash.callback_context.triggered[0][
            'prop_id'] == 'button-submit-stream.n_clicks':
        is_valid, error = helpers.verify_token(token, key, product='stream')
        if is_valid:
            write_result, error = helpers.write_config(home, config)
            if not write_result:
                return error, NONE, '', None
            if videocontent and videofile and videocheck:
                content_type, content_string = videocontent.split(',')
                decoded = base64.b64decode(content_string)
                with open(os.path.join(home, videofile), 'wb') as video:
                    video.write(decoded)
            user_info = ''
            nvidia = ''
            image_tag = ''
            autoboot = '--rm'
            if helpers.get_os() != 'Windows':
                user_info = '--user `id -u`:`id -g`'
            if os.path.exists('/etc/nv_tegra_release'):
                nvidia = '--runtime nvidia --privileged --group-add video'
                image_tag = ':jetson'
            if boot:
                autoboot = '--restart unless-stopped'
            if not helpers.get_image(STREAM_IMAGE):
                helpers.pull_docker(STREAM_IMAGE)
            command = f'docker run {autoboot} -t ' \
                      f'{nvidia} --name stream ' \
                      f'-v "{home}:{USER_DATA}" ' \
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
        is_valid, error = helpers.verify_token(token, key, product='snapshot')
        if is_valid:
            autoboot = '--restart unless-stopped' if boot else '--rm'
            if not helpers.is_valid_port(port):
                return 'Wrong port', NONE, '', None
            if not helpers.get_image(hardware):
                helpers.pull_docker(hardware)
            gpus = '--gpus all' if 'gpu' in hardware else ''
            nvidia = '--runtime nvidia' if 'jetson' in hardware else ''
            command = f'docker run {gpus} {nvidia} {autoboot} ' \
                      f'-t -p {port}:8080 ' \
                      f'-v license:/license ' \
                      f'-e LICENSE_KEY={key} ' \
                      f'-e TOKEN={token} ' \
                      f'{hardware}'
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
    print(CONSOLE_WELCOME)
    if args.debug:
        app.run_server(debug=True, host='0.0.0.0')
    else:
        webbrowser.open('http://127.0.0.1:8050/')

        # Update log levels
        app.logger.setLevel(logging.ERROR)
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *_: None  # type: ignore

        # Start server
        app.run_server(debug=False,
                       host='0.0.0.0',
                       dev_tools_silence_routes_logging=True)
