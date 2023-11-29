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
from dash import Dash, dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
import dash
from datetime import date
import json


"""
Functions
"""


def read_and_preprocessing(path, in_format, start, end):

    # Read data
    #print(f'Reading data ...')
    stream = read_data_from_folder(path, in_format, start, end)

    # Sort data
    #print(f'Sorting data ...')
    stream.sort(['starttime'])
    #print(f'Data spans from {stream[0].stats.starttime} until {stream[-1].stats.endtime}')

    # Merge traces
    #print(f'Merging data ...')
    stream.merge(method=0, fill_value=0)
    trace = stream[0]

    # Filtering 50 Hz
    if filter_50Hz_f:
        #print(f'Filtering 50 Hz signal ...')
        trace.data = obspy.signal.filter.bandstop(trace.data, 49, 51, trace.meta.sampling_rate, corners=8, zerophase=True)

    return trace


def generate_title(tr, prefix_name):
    title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel} '
    f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} '
    f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
    return title


def prepare_fig(trace, prefix_name):
    #print(f'Preparing figure...')
    #print('Updating dates...')
    tr_dec = trace
    # Decimation
    #print(f'Decimation...')
    num_samples = len(tr_dec.data)
    #print(f'{prefix_name} trace has {len(tr_dec.data)} samples...')
    n_pixels = []
    for m in get_monitors():
        n_pixels.append(m.width)

    target_num_samples = max(n_pixels)
    #print(f'Monitor horizontal resolution is {target_num_samples} pixels')
    oversampling_factor = 25
    factor = int(num_samples / (target_num_samples * oversampling_factor))
    if factor > 1:
        tr_dec.decimate(factor, no_filter=True)  # No antialiasing filtering because of lack of stability due to large decimation factor
        print(f'{prefix_name} trace reduced to {len(tr_dec.data)} samples...')
    # Plotting and formatting
    #print(f'Plotting and formating {prefix_name}...')
    df = pd.DataFrame({'data': tr_dec.data, 'times': tr_dec.times('utcdatetime')})  # check for problems with date format
    xlabel = "Date"
    ylabel = "Amplitude"
    title = generate_title(tr_dec, prefix_name)

    fig = px.line(df, x="times", y="data", title=title, labels={'times': xlabel, 'data': ylabel})

    return fig


def update_layout(min_y, max_y, traza, auto_y, title):
    if auto_y == ['autorange']:
        layout = {"yaxis.autorange": True, 'title': title}
    else:
        if min_y is None:
            min_y = traza.data.min() - 1000
        if max_y is None:
            max_y = traza.data.max() + 1000
        layout = {'yaxis': {'range': [min_y, max_y], 'title': title}}
    return layout


parser = argparse.ArgumentParser()
parser.add_argument("conf_path")
args = parser.parse_args()
par_list = list()
with open(args.conf_path, mode="rb") as file:
    for par in yaml.safe_load_all(file):
        par_list.append(par)

st = obspy.Stream([obspy.Trace(), obspy.Trace(), obspy.Trace()])
st_rsam = st.copy()

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}

for i, par in enumerate(par_list):
    print(f'Processing parameter set {i + 1} out of {len(par_list)}')
    path_data = par['paths']['path_data']
    path_output = par['paths']['path_output']
    starttime = par['date_range']['starttime']
    endtime = par['date_range']['endtime']
    filter_50Hz_f = par['filter']['filter_50Hz_f']
    format_in = par['data_format']['format_in']
    a_max = par['plotting']['a_max']
    a_min = par['plotting']['a_min']
    time_interval_one_row = par['day_plotting']['time_interval_one_row']
    fig_format = par['fig_format']
    verbose = par['verbose']

    if starttime:
        starttime = UTCDateTime(starttime)
    if endtime:
        endtime = UTCDateTime(endtime)

    tr = read_and_preprocessing(path_data, format_in, starttime, endtime)
    # Computes RSAM
    tr_rsam = tr.copy()
    n_samples = int(tr_rsam.meta.sampling_rate * 60 * 10)  # Amount to 10 minutes
    tr_rsam.data = uniform_filter1d(abs(tr_rsam.data), size=n_samples)

    st[i] = tr
    st_rsam[i] = tr_rsam

starttime = st[0].stats.starttime
endtime = st[0].stats.endtime
time_tr = st[0].slice(starttime, endtime)
rsam_tr = st_rsam[0].slice(starttime, endtime)
fig1 = prepare_fig(time_tr, 'Plot')
fig2 = prepare_fig(rsam_tr, 'RSAM')
# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
    html.Div(
        ['Select one channel: ',
         dcc.RadioItems(
            id='channel_selector',
            options=[
                {'label': 'Channel X   ', 'value': 'X'},
                {'label': 'Channel Y   ', 'value': 'Y'},
                {'label': 'Channel Z   ', 'value': 'Z'}
            ],
            value='X',
            style={'display': 'inline-block'})],

        style={'textAlign': 'center'}
    ),

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
    dcc.Checklist(id='auto', options=['autorange'], value=['autorange']),
    html.Div('Select the amplitude range (min to max):'),
    dcc.Input(
            id='min',
            type='number',
            value=None
        ),
    dcc.Input(
                id='max',
                type='number',
                value=None
            ),
    dcc.Graph(id='time_plot', figure=fig1),
    #html.Pre(id='relayout-data-1', style=styles['pre']),
    dcc.Checklist(id='auto_RSAM', options=['autorange'], value=['autorange']),
    html.Div('Select the amplitude range (min to max):'),
    dcc.Input(
        id='min_RSAM',
        type='number',
        value=None
    ),
    dcc.Input(
        id='max_RSAM',
        type='number',
        value=None
    ),
    dcc.Graph(id='RSAM', figure=fig2),
    #html.Pre(id='relayout-data-2', style=styles['pre'])
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
    Output('time_plot', 'figure'),
    Output('RSAM', 'figure'),
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
    State('time_plot', 'figure'),
    State('RSAM', 'figure'),
    prevent_initial_call=True)
def update_plot(channel_selector, startdate, enddate, relayoutdata_1, relayoutdata_2, max_y, min_y, max_y_rsam, min_y_rsam, auto_y, auto_y_rsam, fig_1, fig_2):

    if channel_selector == 'X':
        trace = st[0]
        trace_rsam = st_rsam[0]
    elif channel_selector == 'Y':
        trace = st[1]
        trace_rsam = st_rsam[1]
    else:
        trace = st[2]
        trace_rsam = st_rsam[2]
    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)

    if ctx.triggered_id == 'time_plot' or ctx.triggered_id == 'channel_selector':
        if "xaxis.range[0]" in relayoutdata_1:
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])

    if ctx.triggered_id == 'RSAM' or ctx.triggered_id == 'channel_selector':
        if "xaxis.range[0]" in relayoutdata_2:
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])

    time_tr = trace.slice(start_time, end_time)
    rsam_tr = trace_rsam.slice(start_time, end_time)
    title = generate_title(time_tr, 'Plot')
    title_rsam = generate_title(time_tr, 'RSAM')

    if ctx.triggered_id in ['max', 'min', 'max_RSAM', 'min_RSAM', 'auto', 'auto_RSAM']:
        layout = update_layout(min_y, max_y, time_tr, auto_y, title)
        fig_1['layout'] = layout
        layout_rsam = update_layout(min_y_rsam, max_y_rsam, rsam_tr, auto_y_rsam, title_rsam)
        fig_2['layout'] = layout_rsam
    else:
        fig_1 = prepare_fig(trace=time_tr, prefix_name='Plot')
        fig_2 = prepare_fig(trace=rsam_tr, prefix_name='RSAM')
        layout = update_layout(min_y, max_y, time_tr, auto_y, title)
        fig_1['layout'] = layout
        layout_rsam = update_layout(min_y_rsam, max_y_rsam, rsam_tr, auto_y_rsam, title_rsam)
        fig_2['layout'] = layout_rsam

    return fig_1, fig_2


# Main program
if __name__ == "__main__":

    # Run the app
    app.run(debug=False)
