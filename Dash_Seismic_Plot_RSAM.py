"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""

import obspy
import numpy as np
from obspy.core import UTCDateTime
import obspy.signal.filter
from utils import read_data_from_folder
from scipy.ndimage import uniform_filter1d
import plotly.express as px
import pandas as pd
from screeninfo import get_monitors
from dash import Dash, dcc, html, Input, Output, State, ctx
import sys
import webbrowser
from threading import Timer
import os
import signal
import pyautogui
import socket
from seismic_dash_utils import read_and_preprocessing, open_browser, prepare_time_plot, update_layout, prepare_rsam, update_layout_rsam

args = sys.argv
geophone = args[1]
initial_channel = args[2]
start = args[3]
end = args[4]
filt_50Hz = args[5]
format_in = args[6]

oversampling_factor=10

sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock

ST = obspy.Stream([obspy.Trace(), obspy.Trace(), obspy.Trace()])
channels = ['X', 'Y', 'Z']

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}
path_root = './data/CSIC_LaPalma'

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

for i in range(0, 3):
    data_path = path_root + '_' + geophone + '_' + channels[i]
    print(data_path)
    TR = read_and_preprocessing(data_path, format_in, starttime, endtime, filter_50Hz_f)
    ST[i] = TR.copy()

del TR
if initial_channel == 'X':
    TR = ST[0].copy()
elif initial_channel == 'Y':
    TR = ST[1].copy()
else:
    TR = ST[2].copy()
TR_RSAM = TR.copy()
starttime = TR.stats.starttime
endtime = TR.stats.endtime

fig1 = prepare_time_plot(TR, oversampling_factor)
layout = update_layout(fig1['layout'], None, None, ['autorange'], fig1)
fig1['layout'] = layout
fig2 = prepare_rsam(TR, oversampling_factor)

TR_max = np.max(fig1['data'][0]['y'])
TR_min = np.min(fig1['data'][0]['y'])

del TR

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
         html.Button('Close app', id='kill_button', n_clicks=0)]
    ),
    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto', options=['autorange'], value=['autorange']),
                      html.Div('Amplitude range (min to max):'),
                      dcc.Input(
                          id='min',
                          type='number',
                          value=TR_min,
                          debounce=True),
                      ' ',
                      dcc.Input(
                          id='max',
                          type='number',
                          value=TR_max,
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
    Input('channel_selector', 'value'),
    Input('startdate', 'value'),
    Input('enddate', 'value'),
    Input('time_plot', 'relayoutData'),
    Input('RSAM', 'relayoutData'),
    Input('max', 'value'),
    Input('min', 'value'),
    Input('max_RSAM', 'value'),
    Input('min_RSAM', 'value'),
    Input('auto', 'value'),
    Input('auto_RSAM', 'value'),
    Input('kill_button', 'n_clicks'),
    Input('geophone_selector', 'value'),
    State('time_plot', 'figure'),
    State('RSAM', 'figure')
)
def update_plot(channel_selector, startdate, enddate, relayoutdata_1, relayoutdata_2, max_y, min_y, max_y_rsam,
                min_y_rsam, auto_y, auto_y_rsam, button, geo_sel, fig_1, fig_2):
    print(f'El trigger es {ctx.triggered_id}')
    if ctx.triggered_id == 'kill_button':
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)
    if ctx.triggered_id == 'geophone_selector':
        st_length = len(ST[0])
        ST[0].data = np.zeros(st_length)
        ST[1].data = np.zeros(st_length)
        ST[2].data = np.zeros(st_length)
        for j in range(0, 3):
            path = path_root + '_' + geo_sel + '_' + channels[j]
            print(path)
            tr = read_and_preprocessing(path, format_in, starttime, endtime, filter_50Hz_f)
            ST[j] = tr.copy()
        del tr
    if channel_selector == 'X':
        trace = ST[0].copy()
    elif channel_selector == 'Y':
        trace = ST[1].copy()
    else:
        trace = ST[2].copy()

    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)

    if ctx.triggered_id in ['time_plot']:
        if "xaxis.range[0]" in relayoutdata_1:
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])

    elif ctx.triggered_id in ['RSAM']:
        if "xaxis.range[0]" in relayoutdata_2:
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])

    tr = trace.slice(start_time, end_time)
    tr_rsam = tr.copy()

    if ctx.triggered_id in ['max', 'min', 'max_RSAM', 'min_RSAM', 'auto', 'auto_RSAM']:
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
        fig_1['layout'] = layout
        layout_rsam = update_layout_rsam(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
        fig_2['layout'] = layout_rsam

    if ctx.triggered_id not in ['max', 'min', 'max_RSAM', 'min_RSAM', 'auto', 'auto_RSAM']:

        fig_1 = prepare_time_plot(tr, oversampling_factor)
        fig_2 = prepare_rsam(tr_rsam, oversampling_factor)
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
        fig_1['layout'] = layout
        layout_rsam = update_layout_rsam(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
        fig_2['layout'] = layout_rsam

    return fig_1, fig_2, {'autosize': True}, {'autosize': True}


# Main program
# Run the app
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)


