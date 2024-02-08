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
                                prepare_time_plot_3_channels, correct_data_anomalies, get_start_end_time,
                                get_3_channel_figures, update_layout_3_channels)


args = sys.argv
geophone = args[1]
start = args[2]
end = args[3]
filt_50Hz = args[4]
format_in = args[5]

oversampling_factor = 100
sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock

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


[fig1, fig2, fig3, starttime, endtime] = get_3_channel_figures(starttime, endtime, geophone, filter_50Hz_f, path_root, oversampling_factor, format_in)



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
         '  ',
         html.Button('Read new data', id='update', n_clicks=0),
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
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_x',
                          type='number',
                          value=0,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_y', options=['autorange'], value=['autorange']),
                      html.Div('Channel Y amplitude range (min to max)'),
                      dcc.Input(
                          id='min_y',
                          type='number',
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_y',
                          type='number',
                          value=0,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_z', options=['autorange'], value=['autorange']),
                      html.Div('Channel Z amplitude range (min to max)'),
                      dcc.Input(
                          id='min_z',
                          type='number',
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_z',
                          type='number',
                          value=0,
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
    Output('startdate', 'value'),
    Output('enddate', 'value'),
    State('startdate', 'value'),
    State('enddate', 'value'),
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
    State('geophone_selector', 'value'),
    Input('update', 'n_clicks'),
    State('x_plot', 'figure'),
    State('y_plot', 'figure'),
    State('z_plot', 'figure'),
)
def update_plot(starttime_app, endtime_app, relayoutdata_1, relayoutdata_2, relayoutdata_3, max_x, min_x, max_y,
                min_y, max_z, min_z, auto_x, auto_y, auto_z, button, geo_sel, update, fig_1, fig_2, fig_3):

    start_time = UTCDateTime(starttime_app)
    end_time = UTCDateTime(endtime_app)
    print(f'El trigger es {ctx.triggered_id}')
    if ctx.triggered_id is not None:
        if ctx.triggered_id == 'kill_button':
            pyautogui.hotkey('ctrl', 'w')
            pid = os.getpid()
            os.kill(pid, signal.SIGTERM)

        if ctx.triggered_id == 'update':
            [fig_1, fig_2, fig_3, start_time, end_time] = get_3_channel_figures(start_time, end_time, geo_sel,
                                                                                filter_50Hz_f, path_root,
                                                                                oversampling_factor, format_in)

        if ctx.triggered_id in ['plot_x', 'plot_y', 'plot_z']:
            if "xaxis.range[0]" in relayoutdata_1:
                print('rel_1')
                start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
                end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])
                fig_2['layout']['xaxis']['autorange'] = False
                fig_2['layout']['xaxis']['range'] = [start_time, end_time]

                fig_3['layout']['xaxis']['autorange'] = False
                fig_3['layout']['xaxis']['range'] = [start_time, end_time]


            elif "xaxis.range[0]" in relayoutdata_2:
                print('rel_2')
                start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
                end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])
                fig_1['layout']['xaxis']['autorange'] = False
                fig_1['layout']['xaxis']['range'] = [start_time, end_time]

                fig_3['layout']['xaxis']['autorange'] = False
                fig_3['layout']['xaxis']['range'] = [start_time, end_time]


            elif "xaxis.range[0]" in relayoutdata_3:
                print('rel_3')
                start_time = UTCDateTime(relayoutdata_3['xaxis.range[0]'])
                end_time = UTCDateTime(relayoutdata_3['xaxis.range[1]'])
                fig_1['layout']['xaxis']['autorange'] = False
                fig_1['layout']['xaxis']['range'] = [start_time, end_time]

                fig_2['layout']['xaxis']['autorange'] = False
                fig_2['layout']['xaxis']['range'] = [start_time, end_time]

            else:
                print('autosize')
                start_time = UTCDateTime(fig_1['data'][0]['x'][0])
                end_time = UTCDateTime(fig_1['data'][0]['x'][-1])

                fig_1['layout']['xaxis']['autorange'] = True
                fig_2['layout']['xaxis']['autorange'] = True
                fig_3['layout']['xaxis']['autorange'] = True


        print(start_time)
        print(end_time)
        layout1 = update_layout_3_channels(fig_1, start_time, end_time, min_x, max_x, auto_x)
        fig_1['layout'] = layout1
        layout2 = update_layout_3_channels(fig_2, start_time, end_time, min_y, max_y, auto_y)
        fig_2['layout'] = layout2
        layout3 = update_layout_3_channels(fig_3, start_time, end_time, min_z, max_z, auto_z)
        fig_3['layout'] = layout3

    return (fig_1, fig_2, fig_3, {'autosize': True}, {'autosize': True}, {'autosize': True},
            start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S"))


 # Run the app
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)
