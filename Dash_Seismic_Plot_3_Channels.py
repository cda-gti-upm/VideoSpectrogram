"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""

from obspy.core import UTCDateTime
import obspy.signal.filter
import numpy as np
from dash import Dash, dcc, html, Input, Output, ctx, State
import sys
from threading import Timer
import os
import signal
import pyautogui
import socket
from seismic_dash_utils import (read_and_preprocessing, open_browser, prepare_time_plot, update_layout,
                                prepare_time_plot_3_channels, correct_data_anomalies)


args = sys.argv
geophone = args[1]
start = args[2]
end = args[3]
filt_50Hz = args[4]
format_in = args[5]

oversampling_factor = 10
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

starttime = ST[0].stats.starttime
endtime = ST[0].stats.endtime

TRACE_X = ST[0].slice(starttime, endtime)
TRACE_Y = ST[1].slice(starttime, endtime)
TRACE_Z = ST[2].slice(starttime, endtime)

fig1 = prepare_time_plot_3_channels(TRACE_X, oversampling_factor, 'X')
fig2 = prepare_time_plot_3_channels(TRACE_Y, oversampling_factor, 'Y')
fig3 = prepare_time_plot_3_channels(TRACE_Z, oversampling_factor, 'Z')


TR_x_max = np.max(fig1['data'][0]['y'])
TR_x_min = np.min(fig1['data'][0]['y'])
TR_y_max = np.max(fig2['data'][0]['y'])
TR_y_min = np.min(fig2['data'][0]['y'])
TR_z_max = np.max(fig3['data'][0]['y'])
TR_z_min = np.min(fig3['data'][0]['y'])

del TRACE_X
del TRACE_Y
del TRACE_Z

# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
    dcc.Dropdown(['Geophone1', 'Geophone2', 'Geophone3', 'Geophone4',
                  'Geophone5', 'Geophone6', 'Geophone7', 'Geophone8'], id='geophone_selector', value=geophone),
    html.Div(
        ['Select the start and end time (format: yyyy-mm-dd hh:mm:ss): ',
         dcc.Input(
             id='startdate',
             type='text',
             value=starttime.strftime("%Y-%m-%d %H:%M:%S"),
             style={'display': 'inline-block'},
             debounce=True
         ),
         dcc.Input(
             id='enddate',
             type='text',
             value=endtime.strftime("%Y-%m-%d %H:%M:%S"),
             debounce=True,
             style={'display': 'inline-block'},),
         '   ',
         html.Button('Close app', id='kill_button', n_clicks=0)],
    ),
    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto_x', options=['autorange'], value=['autorange']),
                      html.Div('Channel X amplitude range (min to max)'),
                      dcc.Input(
                          id='min_x',
                          type='number',
                          value=TR_x_min,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_x',
                          type='number',
                          value=TR_x_max,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_y', options=['autorange'], value=['autorange']),
                      html.Div('Channel Y amplitude range (min to max)'),
                      dcc.Input(
                          id='min_y',
                          type='number',
                          value=TR_y_min,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_y',
                          type='number',
                          value=TR_y_max,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_z', options=['autorange'], value=['autorange']),
                      html.Div('Channel Z amplitude range (min to max)'),
                      dcc.Input(
                          id='min_z',
                          type='number',
                          value=TR_z_min,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_z',
                          type='number',
                          value=TR_z_max,
                          debounce=True
                      )],
            style={'display': 'in-line-block'})],
        style={'display': 'flex'}),
    dcc.Graph(id='x_plot', figure=fig1, style={'width': '170vh', 'height': '25vh'}),
    dcc.Graph(id='y_plot', figure=fig2, style={'width': '170vh', 'height': '25vh'}),
    dcc.Graph(id='z_plot', figure=fig3, style={'width': '170vh', 'height': '25vh'})
])


@app.callback(
    Output('x_plot', 'figure'),
    Output('y_plot', 'figure'),
    Output('z_plot', 'figure'),
    Output('x_plot', 'relayoutData'),
    Output('y_plot', 'relayoutData'),
    Output('z_plot', 'relayoutData'),
    Input('startdate', 'value'),
    Input('enddate', 'value'),
    Input('x_plot', 'relayoutData'),
    Input('y_plot', 'relayoutData'),
    Input('z_plot', 'relayoutData'),
    Input('max_x', 'value'),
    Input('min_x', 'value'),
    Input('max_y', 'value'),
    Input('min_y', 'value'),
    Input('max_z', 'value'),
    Input('min_z', 'value'),
    Input('auto_x', 'value'),
    Input('auto_y', 'value'),
    Input('auto_z', 'value'),
    Input('kill_button', 'n_clicks'),
    Input('geophone_selector', 'value'),
    State('x_plot', 'figure'),
    State('y_plot', 'figure'),
    State('z_plot', 'figure'),
)
def update_plot(startdate, enddate, relayoutdata_1, relayoutdata_2, relayoutdata_3, max_x, min_x, max_y,
                min_y, max_z, min_z, auto_x, auto_y, auto_z, button, geo_sel, fig_1, fig_2, fig_3):
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

    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)

    if ctx.triggered_id == 'x_plot':
        if "xaxis.range[0]" in relayoutdata_1:
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])
    if ctx.triggered_id == 'y_plot':
        if "xaxis.range[0]" in relayoutdata_2:
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])
    if ctx.triggered_id == 'z_plot':
        if "xaxis.range[0]" in relayoutdata_3:
            start_time = UTCDateTime(relayoutdata_3['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_3['xaxis.range[1]'])

    tr_x = ST[0].slice(start_time, end_time)
    tr_y = ST[1].slice(start_time, end_time)
    tr_z = ST[2].slice(start_time, end_time)


    if ctx.triggered_id in ['max_x', 'min_x', 'max_y', 'min_y', 'max_z', 'min_z', 'auto_x', 'auto_y', 'auto_z']:

        layout1 = update_layout(fig_1['layout'], min_x, max_x, auto_x, fig_1)
        fig_1['layout'] = layout1
        layout2 = update_layout(fig_2['layout'], min_y, max_y, auto_y, fig_2)
        fig_2['layout'] = layout2
        layout3 = update_layout(fig_3['layout'], min_z, max_z, auto_z, fig_3)
        fig_3['layout'] = layout3

    else:
        fig_1 = prepare_time_plot_3_channels(tr_x, oversampling_factor, 'X')
        fig_2 = prepare_time_plot_3_channels(tr_y, oversampling_factor, 'Y')
        fig_3 = prepare_time_plot_3_channels(tr_z, oversampling_factor, 'Z')
        layout1 = update_layout(fig_1['layout'], min_x, max_x, auto_x, fig_1)
        fig_1['layout'] = layout1
        layout2 = update_layout(fig_2['layout'], min_y, max_y, auto_y, fig_2)
        fig_2['layout'] = layout2
        layout3 = update_layout(fig_3['layout'], min_z, max_z, auto_z, fig_3)
        fig_3['layout'] = layout3

    return fig_1, fig_2, fig_3, {'autosize': True}, {'autosize': True}, {'autosize': True}


 # Run the app
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)
