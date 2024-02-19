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
from seismic_dash_utils import read_and_preprocessing, open_browser, prepare_spectrogram, prepare_time_plot, update_layout
import socket
import plotly.graph_objs as go





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

oversampling_factor = 25  # The higher, the more samples in the amplitude figure

if start:
    STARTTIME = UTCDateTime(start)
else:
    STARTTIME = None
if end:
    ENDTIME = UTCDateTime(end)
else:
    ENDTIME = None


if filt_50Hz == 's':
    filter_50Hz_f = True
else:
    filter_50Hz_f = False


path_root = f'./data/CSIC_{location}'
data_path = path_root + '_' + GEOPHONE + '_' + CHANNEL

TR = read_and_preprocessing(data_path, format_in, STARTTIME, ENDTIME, filter_50Hz_f)

STARTTIME = TR.stats.starttime
ENDTIME = TR.stats.endtime

# Creating app layout:

app = Dash(__name__)
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
         html.Button('Read new data', id='update', n_clicks=0),
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

    dcc.Graph(id='time_plot', figure=go.Figure(), style={'width': '164.5vh', 'height': '30vh'}, relayoutData={'autosize': True}),
    dcc.Graph(id='spectrogram', figure=go.Figure(), style={'width': '170vh', 'height': '50vh'}, relayoutData={'autosize': True})
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
    Input('startdate', 'value'),
    Input('enddate', 'value'),
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
def update(geo_sel, channel_selector, startdate, enddate, relayoutdata_1, relayoutdata_2, max_y, min_y, max_freq,
           min_freq, auto_y, button, export_button, update, s_min, s_max, fig_1, fig_2):

    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)
    global TR
    global CHANNEL
    global GEOPHONE
    global STARTTIME
    global ENDTIME

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
        if channel_selector != CHANNEL or geo_sel != GEOPHONE or STARTTIME != start_time or ENDTIME != end_time:  # Read new data only if a parameter is changed
            # Read new data
            CHANNEL = channel_selector
            GEOPHONE = geo_sel
            STARTTIME = start_time
            ENDTIME = end_time
            TR.data = np.zeros(len(TR))
            path = path_root + '_' + geo_sel + '_' + channel_selector
            TR = read_and_preprocessing(path, format_in, start_time, end_time, filter_50Hz_f)
            tr = TR.slice(start_time, end_time)
            fig_2 = prepare_spectrogram(tr=tr, s_min=s_min, s_max=s_max, hop_length=hop_length, win_length=win_length, n_fft=n_fft, window=window)
            fig_1 = prepare_time_plot(tr=tr, oversampling_factor=oversampling_factor)
            fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
            start_time = TR.stats.starttime
            end_time = TR.stats.endtime
            if len(tr) != 0:
                layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
                fig_1['layout'] = layout

    else:
        if ctx.triggered_id == 'time_plot':
            if "xaxis.range[0]" in relayoutdata_1:
                # Get start and end time the user selected on the amplitude plot
                start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
                end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])

        if ctx.triggered_id == 'spectrogram':
            if "xaxis.range[0]" in relayoutdata_2:
                # Get start and end time the user selected on the spectrogram
                start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
                end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])

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

        if ctx.triggered_id not in ['max', 'min', 'auto', 'max_freq', 'min_freq', 'Smax', 'Smin']:
            tr = TR.slice(start_time, end_time)
            fig_2 = prepare_spectrogram(tr=tr, s_min=s_min, s_max=s_max, hop_length=hop_length, win_length=win_length,
                                        n_fft=n_fft, window=window)
            fig_1 = prepare_time_plot(tr=tr, oversampling_factor=oversampling_factor)
            fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
            start_time = TR.stats.starttime
            end_time = TR.stats.endtime
            if len(tr) != 0:
                layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
                fig_1['layout'] = layout

    print('Done!')
    return (fig_1, fig_2, {'autosize': True}, {'autosize': True},
            start_time.strftime("%Y-%m-%d %H:%M:%S.%f"), end_time.strftime("%Y-%m-%d %H:%M:%S.%f"))


# Run the app
Timer(5, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)


