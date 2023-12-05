"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""

import os
import librosa.display
import matplotlib.dates
from tqdm import tqdm
import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator, AutoLocator, MaxNLocator)
from utils import read_data_from_folder
import numpy as np
import argparse
import yaml
import pickle
from scipy.ndimage import uniform_filter1d
import plotly.express as px
import pandas as pd
from screeninfo import get_monitors
from dash import Dash, dcc, html, Input, Output, ctx, State
from datetime import date


"""
Functions
"""


def read_and_preprocessing(path, in_format, start, end):

    # Read data
    print(f'Reading data ...')
    stream = read_data_from_folder(path, in_format, start, end)

    # Sort data
    print(f'Sorting data ...')
    stream.sort(['starttime'])
    print(f'Data spans from {stream[0].stats.starttime} until {stream[-1].stats.endtime}')

    # Merge traces
    print(f'Merging data ...')
    stream.merge(method=0, fill_value=0)
    trace = stream[0]

    # Filtering 50 Hz
    if filter_50Hz_f:
        print(f'Filtering 50 Hz signal ...')
        trace.data = obspy.signal.filter.bandstop(trace.data, 49, 51, trace.meta.sampling_rate, corners=8, zerophase=True)

    return trace


def generate_title(tr, prefix_name):
    title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel} '
    f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} '
    f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
    return title


def prepare_fig(tr, prefix_name):
    print(f'Preparing figure...')
    print('Updating dates...')
    # Decimation
    print(f'Decimation...')
    num_samples = len(tr.data)
    print(f'{prefix_name} trace has {len(tr.data)} samples...')
    n_pixels = []
    for m in get_monitors():
        n_pixels.append(m.width)

    target_num_samples = max(n_pixels)
    print(f'Monitor horizontal resolution is {target_num_samples} pixels')
    oversampling_factor = 25
    factor = int(num_samples / (target_num_samples * oversampling_factor))
    if factor > 1:
        tr.decimate(factor, no_filter=True)
        print(f'{prefix_name} trace reduced to {len(tr.data)} samples...')
    # Plotting and formatting
    print(f'Plotting and formating {prefix_name}...')
    df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})  # check for problems with date format
    xlabel = "Date"
    ylabel = "Amplitude"
    title = generate_title(tr, prefix_name)

    fig = px.line(df, x="times", y="data", title='', labels={'times': xlabel, 'data': ylabel})
    fig['layout']['title'] = {'text': title, 'x': 0.5}
    fig['layout']['yaxis']['autorange'] = True
    return fig


def update_layout(layout, min_y, max_y, auto_y):
    if (auto_y == ['autorange']) or (min_y is None) or (max_y is None):
        layout['yaxis']['autorange'] = True
    else:
        layout['yaxis']['autorange'] = False
        layout['yaxis']['range'] = [min_y, max_y]
    return layout


parser = argparse.ArgumentParser()
parser.add_argument("conf_path")
args = parser.parse_args()
par_list = list()
with open(args.conf_path, mode="rb") as file:
    for par in yaml.safe_load_all(file):
        par_list.append(par)

global ST
ST = obspy.Stream([obspy.Trace(), obspy.Trace(), obspy.Trace()])

global channels
channels = ['X', 'Y', 'Z']

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}
path_data = par['paths']['path_data']
starttime = par['date_range']['starttime']
endtime = par['date_range']['endtime']
filter_50Hz_f = par['filter']['filter_50Hz_f']
format_in = par['data_format']['format_in']
geophone = par['geophone']['geophone_name']
if starttime:
    starttime = UTCDateTime(starttime)
if endtime:
    endtime = UTCDateTime(endtime)


for i in range(0, 3):
    data_path = path_data + '_' + geophone + '_' + channels[i]
    print(data_path)
    TR = read_and_preprocessing(data_path, format_in, starttime, endtime)
    ST[i] = TR

del TR

starttime = ST[0].stats.starttime
endtime = ST[0].stats.endtime

TRACE_X = ST[0].slice(starttime, endtime)
TRACE_Y = ST[1].slice(starttime, endtime)
TRACE_Z = ST[2].slice(starttime, endtime)

fig1 = prepare_fig(TRACE_X, 'Plot')
fig2 = prepare_fig(TRACE_Y, 'Plot')
fig3 = prepare_fig(TRACE_Z, 'Plot')

del TRACE_X
del TRACE_Y
del TRACE_Z

# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
    dcc.Dropdown(['Geophone1','Geophone2','Geophone3','Geophone4','Geophone5','Geophone6','Geophone7','Geophone8'],id='geophone_selector', value=geophone),
    html.Div(
        ['Select the start and end time (format: yyyy-mm-dd hh:mm:ss): ',
         dcc.Input(
             id='startdate',
             type='text',
             value=starttime.strftime("%Y-%m-%d %H:%M:%S"),
             style={'display': 'inline-block'}
         ),
         dcc.Input(
             id='enddate',
             type='text',
             value=endtime.strftime("%Y-%m-%d %H:%M:%S"),
             style={'display': 'inline-block'})],

        style={'textAlign': 'center'}
    ),
    dcc.Checklist(id='auto_x', options=['autorange'], value=['autorange']),
    html.Div('Select the amplitude range (min to max):'),
    dcc.Input(
            id='min_x',
            type='number',
            value=None
        ),
    dcc.Input(
                id='max_x',
                type='number',
                value=None
            ),
    dcc.Graph(id='x_plot', figure=fig1),
    #html.Pre(id='relayout-data-1', style=styles['pre']),
    dcc.Checklist(id='auto_y', options=['autorange'], value=['autorange']),
    html.Div('Select the amplitude range (min to max):'),
    dcc.Input(
        id='min_y',
        type='number',
        value=None
    ),
    dcc.Input(
        id='max_y',
        type='number',
        value=None
    ),
    dcc.Graph(id='y_plot', figure=fig2),
    #html.Pre(id='relayout-data-2', style=styles['pre'])
    dcc.Checklist(id='auto_z', options=['autorange'], value=['autorange']),
    html.Div('Select the amplitude range (min to max):'),
    dcc.Input(
        id='min_z',
        type='number',
        value=None
    ),
    dcc.Input(
        id='max_z',
        type='number',
        value=None
    ),
    dcc.Graph(id='z_plot', figure=fig3),
])

'''
@app.callback(Output('relayout-data-1', 'children'),
              [Input('time_plot', 'relayoutData')])
def display_relayout_data(relayoutdata):
    return json.dumps(relayoutdata, indent=2)


@app.callback(Output('relayout-data-2', 'children'),
              [Input('RSAM', 'relayoutData')])
def display_relayout_data(relayoutdata):
    return json.dumps(relayoutdata, indent=2)
'''


@app.callback(
    Output('x_plot', 'figure'),
    Output('y_plot', 'figure'),
    Output('z_plot', 'figure'),
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
    Input('geophone_selector', 'value'),
    State('x_plot', 'figure'),
    State('y_plot', 'figure'),
    State('z_plot', 'figure'),
    prevent_initial_call=True)
def update_plot(startdate, enddate, relayoutdata_1, relayoutdata_2, relayoutdata_3, max_x, min_x, max_y,
                min_y, max_z, min_z, auto_x, auto_y, auto_z, geo_sel, fig_1, fig_2, fig_3):

    if ctx.triggered_id == 'geophone_selector':
        for j in range(0, 3):
            path = path_data + '_' + geo_sel + '_' + channels[j]
            print(path)
            tr = read_and_preprocessing(path, format_in, starttime, endtime)
            ST[j] = tr

        del tr

    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)

    if ctx.triggered_id == 'x_plot':
        if "xaxis.range[0]" in relayoutdata_1:
            print(relayoutdata_1)
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])
    if ctx.triggered_id == 'y_plot':
        if "xaxis.range[0]" in relayoutdata_2:
            print(relayoutdata_2)
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])
    if ctx.triggered_id == 'z_plot':
        if "xaxis.range[0]" in relayoutdata_3:
            print(relayoutdata_3)
            start_time = UTCDateTime(relayoutdata_3['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_3['xaxis.range[1]'])

    trace_x = ST[0]
    trace_y = ST[1]
    trace_z = ST[2]

    tr_x = trace_x.slice(start_time, end_time)
    tr_y = trace_y.slice(start_time, end_time)
    tr_z = trace_z.slice(start_time, end_time)

    if ctx.triggered_id in ['max_x', 'min_x', 'max_y', 'min_y', 'max_z', 'min_z' 'auto_x', 'auto_y', 'auto_z']:
        print('actualizo')
        layout1 = update_layout(fig_1['layout'], min_x, max_x, auto_x)
        fig_1['layout'] = layout1
        layout2 = update_layout(fig_2['layout'], min_y, max_y, auto_y)
        fig_2['layout'] = layout2
        layout3 = update_layout(fig_3['layout'], min_z, max_z, auto_z)
        fig_3['layout'] = layout3

    else:
        print('genero nueva grafica')
        fig_1 = prepare_fig(tr=tr_x, prefix_name='Plot')
        fig_2 = prepare_fig(tr=tr_y, prefix_name='Plot')
        fig_3 = prepare_fig(tr=tr_z, prefix_name='Plot')
        layout1 = update_layout(fig_1['layout'], min_x, max_x, auto_x)
        fig_1['layout'] = layout1
        layout2 = update_layout(fig_2['layout'], min_y, max_y, auto_y)
        fig_2['layout'] = layout2
        layout3 = update_layout(fig_3['layout'], min_z, max_z, auto_z)
        fig_3['layout'] = layout3

    return fig_1, fig_2, fig_3


# Main program
if __name__ == "__main__":

    # Run the app
    app.run(debug=False)