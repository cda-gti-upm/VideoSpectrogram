"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""


import numpy as np
from obspy.core import UTCDateTime
from dash import Dash, dcc, html, Input, Output, State, ctx
import sys
from threading import Timer
import os
import signal
import pyautogui
import socket
from seismic_dash_utils import (read_and_preprocessing, open_browser, prepare_time_plot,
                                update_layout, prepare_rsam, update_layout_rsam)


# Get arguments
args = sys.argv
geophone = args[1]
initial_channel = args[2]
start = args[3]
end = args[4]
filt_50Hz = args[5]
format_in = args[6]

oversampling_factor = 50  # A higher value gives more samples to the plot

# Get a free random port
sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock


if start:
    starttime = UTCDateTime(start)
else:
    starttime = None
if end:
    endtime = UTCDateTime(end)
else:
    endtime = None

if filt_50Hz == 's':
    filter_50Hz_f = True
else:
    filter_50Hz_f = False


path_root = './data/CSIC_LaPalma'
data_path = path_root + '_' + geophone + '_' + initial_channel
print(f' Data path is: {data_path}')
TR = read_and_preprocessing(data_path, format_in, starttime, endtime, filter_50Hz_f)
trace = TR.copy()
starttime = TR.stats.starttime
endtime = TR.stats.endtime

fig1 = prepare_time_plot(trace, oversampling_factor)
if len(trace) != 0:
    layout = update_layout(fig1['layout'], None, None, ['autorange'], fig1)
    fig1['layout'] = layout

fig2 = prepare_rsam(trace)
del trace


# Creating app layout:
app = Dash(__name__)
app.layout = html.Div([
    dcc.Dropdown(['Geophone1', 'Geophone2', 'Geophone3', 'Geophone4', 'Geophone5', 'Geophone6', 'Geophone7',
                  'Geophone8'], id='geophone_selector', value=geophone),
    html.Div(
        ['Channel: ',
         dcc.RadioItems(
            id='channel_selector',
            options=[
                {'label': 'Channel X   ', 'value': 'X'},
                {'label': 'Channel Y   ', 'value': 'Y'},
                {'label': 'Channel Z   ', 'value': 'Z'}
            ],
            value=initial_channel,
            style={'display': 'inline-block'})]
    ),

    html.Div(
        ['Start and end time (yyyy-mm-dd hh:mm:ss): ',
         dcc.Input(
             id='startdate',
             type='text',
             value=starttime.strftime("%Y-%m-%d %H:%M:%S"),
             style={'display': 'inline-block'},
             debounce=True
         ),
         '  ',
         dcc.Input(
             id='enddate',
             type='text',
             value=endtime.strftime("%Y-%m-%d %H:%M:%S"),
             debounce=True,
             style={'display': 'inline-block'}),
         '  ',
         html.Button('Read new data', id='update', n_clicks=0),
         '  ',
         html.Button('Close app', id='kill_button', n_clicks=0)]
    ),
    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto', options=['autorange'], value=['autorange']),
                      html.Div('Amplitude range (min to max):'),
                      dcc.Input(
                          id='min',
                          type='number',
                          value=0,
                          debounce=True),
                      ' ',
                      dcc.Input(
                          id='max',
                          type='number',
                          value=0,
                          debounce=True)],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_RSAM', options=['autorange'], value=['autorange']),
                      html.Div('RSAM range (min to max):'),
                      dcc.Input(
                          id='min_RSAM',
                          type='number',
                          value=None,
                          debounce=True),
                      ' ',
                      dcc.Input(
                          id='max_RSAM',
                          type='number',
                          value=None,
                          debounce=True)],
            style={'display': 'inline-block'}),],
        style={'display': 'flex'}),

    dcc.Graph(id='time_plot', figure=fig1, style={'width': '170vh', 'height': '40vh'}),
    dcc.Graph(id='RSAM', figure=fig2, style={'width': '170vh', 'height': '40vh'})
])


@app.callback(
    Output('time_plot', 'figure'),
    Output('RSAM', 'figure'),
    Output('time_plot', 'relayoutData'),
    Output('RSAM', 'relayoutData'),
    Output('startdate', 'value'),
    Output('enddate', 'value'),
    State('channel_selector', 'value'),
    State('startdate', 'value'),
    State('enddate', 'value'),
    Input('time_plot', 'relayoutData'),
    Input('RSAM', 'relayoutData'),
    Input('max', 'value'),
    Input('min', 'value'),
    Input('max_RSAM', 'value'),
    Input('min_RSAM', 'value'),
    Input('auto', 'value'),
    Input('auto_RSAM', 'value'),
    Input('kill_button', 'n_clicks'),
    State('geophone_selector', 'value'),
    Input('update', 'n_clicks'),
    State('time_plot', 'figure'),
    State('RSAM', 'figure'),
)
def update_plot(channel_selector, starttime_app, endtime_app, relayoutdata_1, relayoutdata_2, max_y, min_y, max_y_rsam,
                min_y_rsam, auto_y, auto_y_rsam, button, geo_sel, update, fig_1, fig_2):
    global TR

    if ctx.triggered_id == 'kill_button':
        # Close the app
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

    if ctx.triggered_id == 'update':
        # Read new data
        length = len(TR)
        TR.data = np.zeros(length)
        path = path_root + '_' + geo_sel + '_' + channel_selector
        TR = read_and_preprocessing(path, format_in, UTCDateTime(starttime_app), UTCDateTime(endtime_app), filter_50Hz_f)

    start_time = UTCDateTime(starttime_app)
    end_time = UTCDateTime(endtime_app)

    if ctx.triggered_id in ['time_plot']:
        if "xaxis.range[0]" in relayoutdata_1:
            # Get start and end time the user selected on the amplitude plot
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])

    elif ctx.triggered_id in ['RSAM']:
        if "xaxis.range[0]" in relayoutdata_2:
            # Get start and end time the user selected on the RSAM plot
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])


    if ctx.triggered_id in ['max', 'min', 'max_RSAM', 'min_RSAM', 'auto', 'auto_RSAM']:
        # Management of the amplitude ranges
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
        fig_1['layout'] = layout
        layout_rsam = update_layout_rsam(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
        fig_2['layout'] = layout_rsam

    if ctx.triggered_id not in ['max', 'min', 'max_RSAM', 'min_RSAM', 'auto', 'auto_RSAM', None]:
        # Computation of the new trace and figures
        tr = TR.slice(start_time, end_time)
        fig_1 = prepare_time_plot(tr, oversampling_factor)
        fig_2 = prepare_rsam(tr)
        start_time = TR.stats.starttime
        end_time = TR.stats.endtime
        if len(tr) != 0:
            layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
            fig_1['layout'] = layout
            layout_rsam = update_layout_rsam(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
            fig_2['layout'] = layout_rsam

    return (fig_1, fig_2, {'autosize': True}, {'autosize': True}, start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time.strftime("%Y-%m-%d %H:%M:%S"))


# Run the app
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)


