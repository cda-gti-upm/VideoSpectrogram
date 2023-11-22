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
from dash import Dash, dcc, html, Input, Output, callback
from datetime import date


"""
Functions
"""


def read_and_preprocessing():

    # Read data
    print(f'Reading data ...')
    stream = read_data_from_folder(path_data, format_in, starttime, endtime)

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


def prepare_fig(tr, start_time, end_time, prefix_name):
    print(f'Preparing figure...')
    print('Updating dates...')
    tr = tr.slice(start_time, end_time)
    D = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
    frame_indices = np.arange(D.shape[1])
    time_rel = librosa.frames_to_time(frame_indices, sr=tr.meta.sampling_rate, hop_length=hop_length, n_fft=None)
    time_abs = list([tr.stats.starttime + time_rel[0]])
    time_abs[0] = tr.stats.starttime + time_rel[0]
    for i in range(1, len(time_rel)):
        time_abs.append(tr.stats.starttime + time_rel[i])
    freqs = np.arange(0, 1 + n_fft / 2) * tr.meta.sampling_rate / n_fft
    print(freqs)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=1, amin=1e-5, top_db=None)

    fig = px.imshow(S_db, x=time_abs, y=freqs, origin='lower', labels={'x': 'Time', 'y': 'Frequency (Hz)', 'color': 'Power (dB)'},
                    color_continuous_scale='jet')
    # Use the parameters [a_min, a_max] if data values are inside that range. If not use the min and max data
    # values.

    return fig



parser = argparse.ArgumentParser()
parser.add_argument("conf_path")
args = parser.parse_args()
par_list = list()
with open(args.conf_path, mode="rb") as file:
    for par in yaml.safe_load_all(file):
        par_list.append(par)

st = obspy.Stream([obspy.Trace(), obspy.Trace(), obspy.Trace()])

for i, par in enumerate(par_list):
    print(f'Processing parameter set {i + 1} out of {len(par_list)}')
    path_data = par['paths']['path_data']
    path_output = par['paths']['path_output']
    starttime = par['date_range']['starttime']
    endtime = par['date_range']['endtime']
    filter_50Hz_f = par['filter']['filter_50Hz_f']
    format_in = par['data_format']['format_in']
    win_length = par['spectrogram']['win_length']
    hop_length = par['spectrogram']['hop_length']
    n_fft = par['spectrogram']['n_fft']
    window = par['spectrogram']['window']
    spec_interval = par['spectrogram']['spec_interval']
    a_max = par['plotting']['a_max']
    a_min = par['plotting']['a_min']
    S_max = par['plotting']['S_max']
    S_min = par['plotting']['S_min']
    Low_frequency = par['plotting']['Low_frequency']
    High_frequency = par['plotting']['High_frequency']
    time_interval_one_row = par['day_plotting']['time_interval_one_row']
    fig_format = par['fig_format']
    verbose = par['verbose']

    if starttime:
        starttime = UTCDateTime(starttime)
    if endtime:
        endtime = UTCDateTime(endtime)

    tr = read_and_preprocessing()
    st[i] = tr


starttime = st[0].stats.starttime
endtime = st[0].stats.endtime
# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
    html.H1("Welcome to the spectrogram visualizator", style={'textAlign': 'center'}),
    html.Div('Select one channel:'),
    dcc.RadioItems(
        id='channel_selector',
        options=[
            {'label': 'Channel X   ', 'value': 'X'},
            {'label': 'Channel Y   ', 'value': 'Y'},
            {'label': 'Channel Z   ', 'value': 'Z'}
        ],
        value='X'
    ),
    html.Div('Select the start and end time (format: yyyy-mm-dd hh:mm:ss):'),
    dcc.Input(
        id='startdate',
        type='text',
        value=starttime.strftime("%Y-%m-%d %H:%M:%S")
    ),
    dcc.Input(
        id='enddate',
        type='text',
        value=endtime.strftime("%Y-%m-%d %H:%M:%S")
    ),
    dcc.Graph(id='time_plot')
])


@app.callback(
    Output('time_plot', 'figure'),
    Input('channel_selector', 'value'),
    Input('startdate', 'value'),
    Input('enddate', 'value')
)
def update(channel_selector, startdate, enddate):
    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)
    trace = obspy.Trace()
    if channel_selector == 'X':
        trace = st[0]
    elif channel_selector == 'Y':
        trace = st[1]
    else:
        trace = st[2]
    fig1 = prepare_fig(tr=trace, start_time=start_time, end_time=end_time, prefix_name='Spectogram')
    print('Graph updated!')
    return fig1


# Main program

if __name__ == "__main__":
    app.run(debug=False)
    