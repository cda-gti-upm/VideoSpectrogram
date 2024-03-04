"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""

import sys
from obspy.core import UTCDateTime
import numpy as np
from dash import Dash, dcc, html, Input, Output, ctx, State
from threading import Timer
import os
import signal
import pyautogui
from CSIC_Seismic_Visualizator_Utils import read_and_preprocessing, open_browser, prepare_spectrogram, update_layout, prepare_rsam, max_per_window
import socket
import plotly.graph_objs as go
import obspy.signal.filter


# Get arguments
args = sys.argv
GEOPHONE = args[1]
CHANNEL = args[2]
start = args[3]
end = args[4]
filt_50Hz = args[5]
format_in = args[6]
location = args[7]
win_length = int(args[8])
hop_length = int(args[9])
n_fft = int(args[10])
window = args[11]
S_max = int(args[12])
S_min = int(args[13])

# Get a random free port
sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock

oversampling_factor = 2  # The higher, the more samples in the amplitude figure

try:
    if start:
        STARTTIME = UTCDateTime(start, iso8601=True)
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


path_root = './data/CSIC_LaPalma'
data_path = path_root + '_' + GEOPHONE + '_' + CHANNEL

TR = read_and_preprocessing(data_path, format_in, STARTTIME, ENDTIME, filter_50Hz_f)

STARTTIME = TR.stats.starttime
ENDTIME = TR.stats.endtime

# Creating app layout:

app = Dash(__name__, title='Option 1')
app.layout = html.Div([
    dcc.Dropdown(
        ['Geophone1', 'Geophone2', 'Geophone3', 'Geophone4', 'Geophone5', 'Geophone6', 'Geophone7', 'Geophone8'],
        id='geophone_selector', value=GEOPHONE),
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
             style={'display': 'inline-block'})],
    ),
    html.Div(
        ['Start and end time (yyyy-mm-dd hh:mm:ss): ',
         dcc.Input(
             id='startdate',
             type='text',
             value=STARTTIME.strftime("%Y-%m-%d %H:%M:%S.%f"),
             debounce=True,
             style={'display': 'inline-block'}
         ),
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
         html.Button('Close app', id='kill_button', n_clicks=0)],
    ),

    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto', options=['autorange'], value=['autorange']),
                      html.Div('Amplitude range (min to max)'),
                      dcc.Input(
                          id='min',
                          type='number',
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max',
                          type='number',
                          value=0,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[html.Br(),
                      html.Div('Spectrogram frequency range (Hz)'),
                      dcc.Input(
                          id='min_freq',
                          type='number',
                          value=5,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_freq',
                          type='number',
                          value=125,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[html.Br(),
                      html.Div('Spectrogram power range (dB)'),
                      dcc.Input(
                          id='Smin',
                          type='number',
                          value=75,
                          debounce=True
                      ),
                      dcc.Input(
                          id='Smax',
                          type='number',
                          value=130,
                          debounce=True
                      )],
            style={'display': 'in-line-block'})],
        style={'display': 'flex'}),

    dcc.Graph(id='time_plot', figure=go.Figure(), style={'width': '170vh', 'height': '30vh'}, relayoutData={'autosize': True}, config={'modeBarButtonsToRemove': ['pan2d', 'autoScale2d']}),
    dcc.Graph(id='spectrogram', figure=go.Figure(), style={'width': '170vh', 'height': '60vh'}, relayoutData={'autosize': True}, config={'modeBarButtonsToRemove': ['pan2d', 'autoScale2d']})
])


@app.callback(
    Output('time_plot', 'figure'),
    Output('spectrogram', 'figure'),
    Output('time_plot', 'relayoutData'),
    Output('spectrogram', 'relayoutData'),
    Output('startdate', 'value'),
    Output('enddate', 'value'),
    State('geophone_selector', 'value'),
    State('channel_selector', 'value'),
    State('startdate', 'value'),
    State('enddate', 'value'),
    Input('time_plot', 'relayoutData'),
    Input('spectrogram', 'relayoutData'),
    Input('max', 'value'),
    Input('min', 'value'),
    Input('max_freq', 'value'),
    Input('min_freq', 'value'),
    Input('auto', 'value'),
    Input('kill_button', 'n_clicks'),
    Input('export', 'n_clicks'),
    Input('update', 'n_clicks'),
    Input('Smin', 'value'),
    Input('Smax', 'value'),
    State('time_plot', 'figure'),
    State('spectrogram', 'figure')
)
def update(geo_sel, channel_selector, starttime_app, endtime_app, relayoutdata_1, relayoutdata_2, max_y, min_y, max_freq,
           min_freq, auto_y, button, esport_button, update, s_min, s_max, fig_1, fig_2):
    global TR
    global CHANNEL
    global GEOPHONE
    global STARTTIME
    global ENDTIME
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
        print('No valid dates')
    if ctx.triggered_id == 'kill_button':
        # Close the app
        print('Closing app...')
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

    elif ctx.triggered_id == 'export':
        if not os.path.exists("./exports"):
            os.mkdir("./exports")
        fig1 = go.Figure(data=fig_1['data'], layout=fig_1['layout'])
        file_title = fig1['layout']['title']['text']
        fig1.write_image(file=f"./exports/{file_title}.svg", format="svg", width=1920, height=1080, scale=1)
        fig2 = go.Figure(data=fig_2['data'], layout=fig_2['layout'])
        file_title = fig2['layout']['title']['text']
        fig2.write_image(file=f"./exports/{file_title}.svg", format="svg", width=1920, height=1080, scale=1)
        print('Export completed.')

    elif ctx.triggered_id == 'update':
        if channel_selector != CHANNEL or geo_sel != GEOPHONE or start_time < STARTTIME or end_time > ENDTIME:  # Read new data only if a parameter is changed
            # Read new data
            CHANNEL = channel_selector
            GEOPHONE = geo_sel
            STARTTIME = start_time
            ENDTIME = end_time
            TR.data = np.zeros(len(TR))
            path = path_root + '_' + geo_sel + '_' + channel_selector
            TR = read_and_preprocessing(path, format_in, start_time, end_time, filter_50Hz_f)
            compute_graph = True
        elif start_time != fig_1['data'][0]['x'][0] or end_time != fig_1['data'][0]['x'][-1]:
            compute_graph = True

    if ctx.triggered_id == 'time_plot':
        compute_graph = True
        if "xaxis.range[0]" in relayoutdata_1:
            # Get start and end time the user selected on the amplitude plot
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])
        else:
            start_time = STARTTIME
            end_time = ENDTIME
    elif ctx.triggered_id == 'spectrogram':
        compute_graph = True
        if "xaxis.range[0]" in relayoutdata_2:
            # Get start and end time the user selected on the spectrogram
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])
        else:
            start_time = STARTTIME
            end_time = ENDTIME


    if ctx.triggered_id in ['max', 'min', 'auto']:
        # Manage amplitude axis of the amplitude plot
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
        fig_1['layout'] = layout
    elif ctx.triggered_id in ['max_freq', 'min_freq']:
        # Maximum and minimum displayed frequencies
        fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
    elif ctx.triggered_id in ['Smax', 'Smin']:
        # Maximum and minimum displayed spectrogram power values
        fig_2['layout']['coloraxis']['cmax'] = s_max
        fig_2['layout']['coloraxis']['cmin'] = s_min
        #compute_graph = True

    if compute_graph and not dates_error:
        tr = TR.slice(start_time, end_time)
        fig_2 = prepare_spectrogram(tr=tr, s_min=s_min, s_max=s_max, hop_length=hop_length, win_length=win_length, n_fft=n_fft, window=window)
        try:
            """
            tr.data = obspy.signal.filter.bandpass(tr.data, min_freq+0.1, max_freq-0.1, tr.meta.sampling_rate, corners=8,
                                                   zerophase=True)
                                                   """
        except Exception as e_filt:
            print(f'Error when filtering the signal: {e_filt}')
            sys.exit()

        num_samples = len(tr)
        target_num_samples = 1920
        factor = int(num_samples / (target_num_samples * oversampling_factor))
        max_per_window(tr, factor)
        fig_1 = prepare_rsam(tr)
        fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
        if len(tr) != 0:
            layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
            fig_1['layout'] = layout

    start_time = fig_1['data'][0]['x'][0]
    end_time = fig_1['data'][0]['x'][-1]
    if type(start_time) is str:  # First time is UTC, after is string
        start_time = UTCDateTime(start_time)
        end_time = UTCDateTime(end_time)
    print('UPDATE COMPLETED!')
    return (fig_1, fig_2, {'autosize': True}, {'autosize': True},
            start_time.strftime("%Y-%m-%d %H:%M:%S.%f"), end_time.strftime("%Y-%m-%d %H:%M:%S.%f"))


# Run the app
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)


