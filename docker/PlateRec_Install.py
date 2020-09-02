import webbrowser

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

plan_link = 'https://app.platerecognizer.com/accounts/plan/?utm_source=installer&utm_medium=app'

app.layout = html.Div(children=[
    html.H1(children='PlateRec Installer'),
    html.Div(children=[
        html.P('Select the Plate Recognizer product you want to install:'),
        dcc.Dropdown(options=[{
            'label': 'Snapshot SDK',
            'value': 'sdk'
        }, {
            'label': 'Stream',
            'value': 'stream'
        }],
                     value='sdk',
                     id='drop-product')
    ],
             id='div-product'),
    html.Br(),
    html.Div(children=[
        html.P('Select your hardware environment:'),
        dcc.Dropdown(options=[], value='windows', id='drop-hardware')
    ],
             id='div-hardware'),
    html.Br(),
    html.Div(children=[
        html.
        P('Docker is required to run Plate Recognizer. Do you have Docker already installed on your machine?'
         ),
        dcc.Dropdown(options=[{
            'label': 'Yes',
            'value': 'yes'
        }, {
            'label': 'No. Please install Docker for me.',
            'value': 'install'
        }, {
            'label': 'No. I will exit and install Docker on my own.',
            'value': 'exit'
        }],
                     value='yes',
                     id='drop-docker')
    ],
             id='div-docker'),
    html.Br(),
    html.Div(children=[
        html.
        P('Ubuntu is required to run Stream on Windows. Do you have Ubuntu already installed on your machine?'
         ),
        dcc.Dropdown(options=[{
            'label': 'Yes',
            'value': 'yes'
        }, {
            'label': 'No. Please install Ubuntu for me.',
            'value': 'install'
        }, {
            'label': 'No. I will exit and install Ubuntu on my own.',
            'value': 'exit'
        }],
                     value='yes',
                     id='drop-ubuntu')
    ],
             id='div-ubuntu'),
    html.Br(id='br-ubuntu'),
    html.Div(children=[
        html.P(id='p-boot'),
        dcc.Dropdown(options=[{
            'label': 'Yes',
            'value': 'yes'
        }, {
            'label': 'No',
            'value': 'no'
        }],
                     value='yes',
                     id='drop-boot')
    ],
             id='div-boot'),
    html.Br(),
    html.Div(children=[
        html.P(id='p-directory'),
        dcc.Input(value='', type='text', id='input-directory')
    ],
             id='div-directory'),
    html.Br(),
    html.Div(children=[
        html.P(children=[
            'Please enter your Plate Recognizer API Token. Go ',
            html.A('here', href=plan_link), ' to get it.'
        ],
               id='p-token'),
        dcc.Input(value='', type='text', id='input-token')
    ],
             id='div-token'),
    html.Br(),
    html.Div(children=[
        html.P(id='p-key'),
        dcc.Input(value='', type='text', id='input-key')
    ],
             id='div-key'),
    html.Br(),
    html.P(children='', style={'color': 'red'}, id='status'),
    html.Button('Install', id='install-button'),
])


@app.callback([
    Output('drop-hardware', 'options'),
    Output('p-boot', 'children'),
    Output('p-directory', 'children'),
    Output('input-directory', 'value'),
    Output('p-key', 'children')
], [Input('drop-product', 'value')])
def switch_product(product):
    hardwares = [{
        'label': 'Linux',
        'value': 'linux'
    }, {
        'label': 'Windows',
        'value': 'windows'
    }, {
        'label': 'Mac',
        'value': 'mac'
    }, {
        'label': 'Nvidia Jetson',
        'value': 'nvidia_jetson'
    }, {
        'label': 'Nvidia Jetson Xavier',
        'value': 'nvidia_jetson_xavier'
    }]
    p_boot = 'Do you want Docker Container and Snapshot SDK to automatically boot on system startup?'
    p_directory = 'Specify the directory for your Snapshot SDK installation.'
    input_directory = 'C:\\Users\\kyt\\Documents\\SDK'
    p_key = [
        'Please enter the Snapshot SDK License Key. Go ',
        html.A('here', href=plan_link), ' to get it.'
    ]
    if product == 'stream':
        hardwares.pop(2)
        p_boot = p_boot.replace('Snapshot SDK', 'Stream')
        p_directory = p_directory.replace('Snapshot SDK', 'Stream')
        input_directory = input_directory.replace('SDK', 'Stream')
        p_key[0] = p_key[0].replace('Snapshot SDK', 'Stream')
    return hardwares, p_boot, p_directory, input_directory, p_key


@app.callback([Output('div-ubuntu', 'style'),
               Output('br-ubuntu', 'style')],
              [Input('drop-product', 'value'),
               Input('drop-hardware', 'value')])
def show_ubuntu(product, hardware):
    if product == 'stream' and hardware == 'windows':
        return ({'display': 'block'},) * 2
    else:
        return ({'display': 'none'},) * 2


@app.callback([Output('install-button', 'style'),
               Output('status', 'children')],
              [Input('install-button', 'n_clicks')])
def install(n_clicks):
    if n_clicks:
        return {'display': 'none'}, 'Installation...'
    else:
        return None, ''


if __name__ == '__main__':
    if 0:
        webbrowser.open('http://127.0.0.1:8050/')
    app.run_server(debug=False)
