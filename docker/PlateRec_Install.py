import os
import platform
import subprocess
import webbrowser
from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
except ImportError:
    from urllib2 import Request, urlopen  # type: ignore
    from urllib2 import URLError  # type: ignore

EXTERNAL_STYLESHEETS = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
DOCKER_URL = 'https://docs.docker.com/install/'
PLAN_LINK = 'https://app.platerecognizer.com/accounts/plan/?utm_source=installer&utm_medium=app'
IMAGE = 'platerecognizer/alpr-stream'
NONE = {'display': 'none'}
BLOCK = {'display': 'block'}


def get_os():
    os_system = platform.system()
    if os_system == 'Windows':
        return 'Windows'
    elif os_system == 'Linux':
        return 'Linux'
    elif os_system == 'Darwin':
        return 'Mac OS'
    return os_system


def verify_docker_install():
    try:
        subprocess.check_output("docker info".split())
        return True
    except (OSError, subprocess.CalledProcessError) as e:
        print(e)
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


def get_image(image):
    images = subprocess.check_output(
        ['docker', 'images', '--format', '"{{.Repository}}"',
         image]).decode().split('\n')
    return images[0].replace('"', '')


def pull_docker(image=IMAGE):
    if get_container_id(image):
        stop_container(image)
    pull_cmd = f'docker pull {image}:latest'
    os.system(pull_cmd)


def read_config(home):
    config = Path.joinpath(Path(home), 'config.ini')
    conf = ''
    try:
        f = open(config, 'r')
    except IOError:  # file not found
        f = open('base_stream_conf.ini', 'r')
    for line in f:
        conf += line
    f.close()
    return conf


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


def verify_token(token, license_key, get_license=True):
    try:
        req = Request(
            'https://app.platerecognizer.com/v1/stream/license/{}/'.format(
                license_key))
        req.add_header('Authorization', 'Token {}'.format(token))
        urlopen(req).read()
        return True, None
    except URLError as e:
        if '404' in str(e) and get_license:
            return False, 'License Key is incorrect!!'
        elif str(403) in str(e):
            return False, 'Api Token is incorrect!!'
        else:
            return True, None


app = dash.Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)

app.layout = html.Div(children=[
    html.H1(children='PlateRec Installer'),
    html.P('Host OS:'),
    dcc.Input(value=get_os(), type='text', id='input-os', disabled=True),
    html.Br(),
    html.Br(),
    html.P(children=[
        "Docker is not installed, Follow ",
        html.A(DOCKER_URL, href=DOCKER_URL),
        " to install docker for your machine."
    ],
           style=NONE,
           id='p-docker'),
    html.Button('Refresh', style=NONE, id='refresh-docker'),
    html.Div(children=[
        html.P('Docker image found on your system, you may update it:'),
        dcc.Loading(type="circle", children=html.Div(id="loading-update")),
        html.Button('Update', id='update-image'),
        html.Span(' You have the latest version.', style=NONE,
                  id='span-update'),
        html.Br(),
        html.Br(),
    ],
             style=NONE,
             id='div-update'),
    html.Div(children=[
        html.P(children=[
            'Please enter your Plate Recognizer API Token. Go ',
            html.A('here', href=PLAN_LINK), ' to get it.'
        ],
               id='p-token'),
        dcc.Input(value='', type='text', id='input-token'),
        html.Br(),
        html.Br(),
        html.P(children=[
            'Please enter the Stream License Key. Go ',
            html.A('here', href=PLAN_LINK), ' to get it.'
        ],
               id='p-key'),
        dcc.Input(value='', type='text', id='input-key'),
        html.Br(),
        html.Br(),
        html.P('Specify the directory for your Stream installation:'),
        dcc.Input(value=str(Path.joinpath(Path.home(), 'stream')),
                  type='text',
                  id='input-home'),
        html.Br(),
        html.Br(),
        dcc.Checklist(options=[{
            'label':
            'Do you want Stream to automatically boot on system startup?',
            'value': 'yes'
        }],
                      value=[
                          'yes',
                      ],
                      id='check-boot'),
        html.Br(),
        html.P('Stream config:'),
        dcc.Textarea(placeholder='config',
                     value='',
                     style={
                         'width': '70%',
                         'height': '300px',
                         'background-color': 'lightgray',
                         'font-size': '13px'
                     },
                     id='area-config'),
        html.Br(),
        html.P(children='', style={'color': 'red'}, id='p-status'),
        dcc.Loading(type="circle", children=html.Div(id="loading-submit")),
        html.Button('Submit', id='button-submit'),
    ],
             style=NONE,
             id='div-next')
])


@app.callback([
    Output('p-docker', 'style'),
    Output('refresh-docker', 'style'),
    Output('div-next', 'style'),
    Output('div-update', 'style')
], [Input('refresh-docker', 'n_clicks')])
def update_docker(n_clicks):
    if verify_docker_install():
        if get_image(IMAGE):
            return NONE, NONE, BLOCK, BLOCK
        else:
            return NONE, NONE, BLOCK, NONE
    else:
        return BLOCK, BLOCK, NONE, NONE


@app.callback([
    Output('update-image', 'disabled'),
    Output('span-update', 'style'),
    Output('loading-update', 'children')
], [Input('update-image', 'n_clicks')])
def update_image(n_clicks):
    if n_clicks:
        pull_docker()
        return True, {'display': 'inline', 'color': 'green'}, None
    return False, NONE, None


@app.callback(Output('area-config', 'value'), [Input('input-home', 'value')])
def change_path(home):
    return read_config(home)


@app.callback([
    Output('button-submit', 'style'),
    Output('p-status', 'children'),
    Output('loading-submit', 'children')
], [
    Input('button-submit', 'n_clicks'),
    State('input-os', 'value'),
    State('input-token', 'value'),
    State('input-key', 'value'),
    State('input-home', 'value'),
    State('check-boot', 'value'),
    State('area-config', 'value')
])
def submit(n_clicks, os_, token, key, home, boot, config):
    if n_clicks:
        is_valid, error = verify_token(token, key)
        if is_valid:
            if not write_config(home, config):
                return BLOCK, "Cannot use selected directory. Please choose another one.", None
            command = 'docker run --rm -t ' \
                      '--name stream ' \
                      f'-v {home}:/user-data ' \
                      '--user `id -u`:`id -g` ' \
                      f'-e LICENSE_KEY={key} ' \
                      f'-e TOKEN={token} ' \
                      f'{IMAGE}'
            if os_ != 'Windows':
                command = command.replace('-v', '--user `id -u`:`id -g` -v')
            if 'jetson' in os_.lower():  # todo: detect jetson correctly
                command = command.replace(
                    '-t', '--runtime nvidia --privileged --group-add video -t')
                command += ':jetson'
            if boot:
                command = command.replace('--rm', '--restart unless-stopped')
            pull_docker()
            return NONE, command, None
        else:
            return BLOCK, error, None
    else:
        return BLOCK, '', None


if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:8050/')
    app.run_server(debug=False)
