"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""

import time
import numpy as np
from obspy.core import UTCDateTime
from dash import Dash, dcc, html, Input, Output, State, ctx
import sys
from threading import Timer
import os
import signal
import pyautogui
import socket
import plotly.graph_objs as go
from CSIC_Seismic_Visualizator_Utils import (read_and_preprocessing, open_browser, prepare_time_plot,
                                             update_layout, prepare_rsam, update_layout_rsam, create_config)


# Get arguments
args = sys.argv
GEOPHONE = args[1]
CHANNEL = args[2]
start = args[3]
end = args[4]
filt_50Hz = args[5]
format_in = args[6]
location = args[7]
min_y_fig1 = float(args[8])
max_y_fig1 = float(args[9])
auto_y_fig1 = args[10]
min_y_fig2 = float(args[11])
max_y_fig2 = float(args[12])
auto_y_fig2 = args[13]



OPTION = 1

oversampling_factor = 5  # A higher value gives more samples to the plot

# Get a free random port
sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock


try:
    if start:
        STARTTIME = UTCDateTime(start)
    else:
        STARTTIME = None

    if end:
        ENDTIME = UTCDateTime(end)
    else:
        ENDTIME = None
except Exception as e:
    print("Date is not valid. (%s: %s)" % (type(e).__name__, e))
    sys.exit()
if (STARTTIME is not None) and (ENDTIME is not None):
    if STARTTIME > ENDTIME:
        print('Start time is after end time.')
        sys.exit()

if filt_50Hz == 's':
    filter_50Hz_f = True
else:
    filter_50Hz_f = False


auto_y_fig1 = ['autorange'] if auto_y_fig1 == 'autorange' else []
auto_y_fig2 = ['autorange'] if auto_y_fig2 == 'autorange' else []

path_root = f'./data/CSIC_{location}'
data_path = path_root + '_' + GEOPHONE + '_' + CHANNEL
TR = read_and_preprocessing(data_path, format_in, STARTTIME, ENDTIME, filter_50Hz_f)

STARTTIME = TR.stats.starttime
ENDTIME = TR.stats.endtime

# Creating app layout:
app = Dash(__name__, title='Option 1')
app.layout = html.Div([
    dcc.Dropdown(['Geophone1', 'Geophone2', 'Geophone3', 'Geophone4', 'Geophone5', 'Geophone6', 'Geophone7',
                  'Geophone8'], id='geophone_selector', value=GEOPHONE),
    html.Div(
        ['Channel: ',
         dcc.RadioItems(
            id='channel_selector',
            options=[
                {'label': 'Channel X   ', 'value': 'X'},
                {'label': 'Channel Y   ', 'value': 'Y'},
                {'label': 'Channel Z   ', 'value': 'Z'}
            ],
            value=CHANNEL,
            style={'display': 'inline-block'})]
    ),

    html.Div(
        ['Start and end time (yyyy-mm-dd hh:mm:ss): ',
         dcc.Input(
             id='startdate',
             type='text',
             value=STARTTIME.strftime("%Y-%m-%d %H:%M:%S.%f"),
             style={'display': 'inline-block'},
             debounce=True
         ),
         '  ',
         dcc.Input(
             id='enddate',
             type='text',
             value=ENDTIME.strftime("%Y-%m-%d %H:%M:%S.%f"),
             debounce=True,
             style={'display': 'inline-block'}),
         '  ',
         html.Button('Update data', id='update', n_clicks=0),
         '  ',
         html.Button('Export in SVG', id='export', n_clicks=0),
         '  ',
         html.Button('Close app', id='kill_button', n_clicks=0),
         '      ',
         dcc.Input(
             id='config_name',
             type='text',
             value='',
             debounce=True,
             style={'display': 'inline-block'}),
         html.Button('Save config.', id='save_config', n_clicks=0)]
    ),
    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto', options=['autorange'], value=auto_y_fig1),
                      html.Div('Amplitude range (min to max):'),
                      dcc.Input(
                          id='min',
                          type='number',
                          value=min_y_fig1,
                          debounce=True),
                      ' ',
                      dcc.Input(
                          id='max',
                          type='number',
                          value=max_y_fig1,
                          debounce=True)],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_RSAM', options=['autorange'], value=auto_y_fig2),
                      html.Div('RSAM range (min to max):'),
                      dcc.Input(
                          id='min_RSAM',
                          type='number',
                          value=min_y_fig2,
                          debounce=True),
                      ' ',
                      dcc.Input(
                          id='max_RSAM',
                          type='number',
                          value=max_y_fig2,
                          debounce=True)],
            style={'display': 'inline-block'}),],
        style={'display': 'flex'}),

    dcc.Graph(id='time_plot', figure=go.Figure(), style={'width': '170vh', 'height': '40vh'}, relayoutData={'autosize': True}, config={'modeBarButtonsToRemove': ['pan2d', 'autoScale2d']}),
    dcc.Graph(id='RSAM', figure=go.Figure(), style={'width': '170vh', 'height': '40vh'}, relayoutData={'autosize': True}, config={'modeBarButtonsToRemove': ['pan2d', 'autoScale2d']})
])


@app.callback(
    Output('time_plot', 'figure'),
    Output('RSAM', 'figure'),
    Output('time_plot', 'relayoutData'),
    Output('RSAM', 'relayoutData'),
    Output('startdate', 'value'),
    Output('enddate', 'value'),
    State('geophone_selector', 'value'),
    State('channel_selector', 'value'),
    State('startdate', 'value'),
    State('enddate', 'value'),
    State('config_name', 'value'),
    Input('time_plot', 'relayoutData'),
    Input('RSAM', 'relayoutData'),
    Input('max', 'value'),
    Input('min', 'value'),
    Input('max_RSAM', 'value'),
    Input('min_RSAM', 'value'),
    Input('auto', 'value'),
    Input('auto_RSAM', 'value'),
    Input('kill_button', 'n_clicks'),
    Input('export', 'n_clicks'),
    Input('update', 'n_clicks'),
    Input('save_config', 'n_clicks'),
    State('time_plot', 'figure'),
    State('RSAM', 'figure'),
)
def update_plot(geo_sel, channel_selector, starttime_app, endtime_app, config_name, relayoutdata_1, relayoutdata_2, max_y, min_y, max_y_rsam,
                min_y_rsam, auto_y, auto_y_rsam, button, export_button, update, save, fig_1, fig_2):

    global TR
    global CHANNEL
    global GEOPHONE
    global STARTTIME
    global ENDTIME
    ini_exec_time = time.time()
    dates_error = False
    compute_graph = True if ctx.triggered_id is None else False

    try:
        start_time = UTCDateTime(starttime_app)
        end_time = UTCDateTime(endtime_app)
    except Exception as e_dates:
        start_time = fig_1['data'][0]['x'][0]
        end_time = fig_1['data'][0]['x'][-1]
        dates_error = True
        print(f'Dates are wrong: {e_dates}')
    if start_time > end_time:
        start_time = fig_1['data'][0]['x'][0]
        end_time = fig_1['data'][0]['x'][-1]
        dates_error = True
        print('No valid dates')

    if ctx.triggered_id == 'kill_button':
        # Close the app
        print('Closing app ...')
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)
    elif ctx.triggered_id == 'save_config':
        print('Saving configuration...')
        parameters = {'option': OPTION,
                      'start_time': start_time.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                      'end_time': end_time.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                      'geophone': GEOPHONE,
                      'channel': CHANNEL,
                      'filt_50Hz': filt_50Hz,
                      'format_in': format_in,
                      'location': location,
                      'min_y_fig1': str(min_y),
                      'max_y_fig1': str(max_y),
                      'auto_y_fig1': auto_y,
                      'min_y_fig2': str(min_y_rsam),
                      'max_y_fig2': str(max_y_rsam),
                      'auto_y_fig2': auto_y_rsam}
        create_config(parameters, config_name)
    elif ctx.triggered_id == 'export':
        print('Saving figures...')
        if not os.path.exists("./exports"):
            os.mkdir("./exports")
        fig1 = go.Figure(data=fig_1['data'], layout=fig_1['layout'])
        file_title = fig1['layout']['title']['text']
        fig1.write_image(file=f"./exports/{file_title}.svg", format="svg", width=1920, height=1080, scale=1)
        fig2 = go.Figure(data=fig_2['data'], layout=fig_2['layout'])
        file_title = fig2['layout']['title']['text']
        fig2.write_image(file=f"./exports/{file_title}.svg", format="svg", width=1920, height=1080, scale=1)
        print('Export completed!')
    elif ctx.triggered_id == 'update':
        # Read new data
        #  Read new data only if a parameter is changed
        if channel_selector != CHANNEL or geo_sel != GEOPHONE or start_time < STARTTIME or end_time > ENDTIME:
            length = len(TR)
            TR.data = np.zeros(length)
            path = path_root + '_' + geo_sel + '_' + channel_selector
            TR = read_and_preprocessing(path, format_in, start_time, end_time, filter_50Hz_f)
            CHANNEL = channel_selector
            GEOPHONE = geo_sel
            STARTTIME = start_time
            ENDTIME = end_time
            compute_graph = True
        elif start_time != fig_1['data'][0]['x'][0] or end_time != fig_1['data'][0]['x'][-1]:
            compute_graph = True
    elif ctx.triggered_id == 'time_plot':
        compute_graph = True
        if "xaxis.range[0]" in relayoutdata_1:
            # Get start and end time the user selected on the amplitude plot
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])
        else:
            start_time = STARTTIME
            end_time = ENDTIME
    elif ctx.triggered_id == 'RSAM':
        compute_graph = True
        if "xaxis.range[0]" in relayoutdata_2:
            # Get start and end time the user selected on the RSAM plot
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])
        else:
            start_time = STARTTIME
            end_time = ENDTIME

    if ctx.triggered_id in ['max', 'min', 'max_RSAM', 'min_RSAM', 'auto', 'auto_RSAM']:
        # Management of the amplitude ranges
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
        fig_1['layout'] = layout
        layout_rsam = update_layout_rsam(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
        fig_2['layout'] = layout_rsam

    if compute_graph and not dates_error:
        # Computation of the new trace and figures
        tr = TR.slice(start_time, end_time)
        fig_1 = prepare_time_plot(tr, oversampling_factor)
        fig_2 = prepare_rsam(tr)

        if len(tr) != 0:
            layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
            fig_1['layout'] = layout
            layout_rsam = update_layout_rsam(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
            fig_2['layout'] = layout_rsam
            start_time = fig_1['data'][0]['x'][0]
            end_time = fig_1['data'][0]['x'][-1]

    if type(start_time) is str: #First time is UTC, after is string
        start_time = UTCDateTime(start_time)
        end_time = UTCDateTime(end_time)

    print(f'Updating took {round(time.time() - ini_exec_time, 2)} seconds...')
    print('Update completed!')

    return (fig_1, fig_2, {'autosize': True}, {'autosize': True}, start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
            end_time.strftime("%Y-%m-%d %H:%M:%S.%f"))


# Run the app
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)


