"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""
import math
import os
import librosa.display

import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter

from utils import read_data_from_folder
import numpy as np
import argparse
import yaml
from screeninfo import get_monitors
import plotly.express as px
import pandas as pd
from screeninfo import get_monitors
from dash import Dash, dcc, html, Input, Output, ctx

from ltsa.ltsa import seismicLTSA


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


def prepare_fig(trace, start_time, end_time):
    print(f'Preparing figure...')
    print('Updating dates...')
    tr = trace.slice(start_time, end_time)
    n_pixels = []
    for m in get_monitors():
        n_pixels.append(m.width)

    res = max(n_pixels)
    num_samples = math.ceil(len(tr.data) / hop_length)
    if num_samples > (res * 10):
        print('COMPUTATION OF LTSA')
        d = seismicLTSA(tr.data, tr.meta.sampling_rate)
        params = {'div_len': int(np.round(len(tr.data)/res)),  # Length in numer of samples
                  'subdiv_len': win_length,
                  'nfft': n_fft,
                  'noverlap': hop_length}
        d.set_params(params)
        print(params['div_len'])

        # compute the LTSA -- identical to s.compute()
        d.compute(ref=1, amin=1e-5, top_db=None)
        S_db = d.ltsa
        frame_indices = np.arange(S_db.shape[1])
        time_rel = (np.asanyarray(frame_indices) * d.div_len + (d.div_len / 2)).astype(int) / float(tr.meta.sampling_rate)
        freqs = np.arange(0, n_fft / 2) * tr.meta.sampling_rate / n_fft
        print(S_db.shape)

    else:
        print('COMPUTATION OF COMPLETE SPECTROGRAM')
        d = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
        S_db = librosa.amplitude_to_db(np.abs(d), ref=1, amin=1e-5, top_db=None)
        print(S_db.shape)
        print(len(tr.data))
        frame_indices = np.arange(d.shape[1])
        time_rel = librosa.frames_to_time(frame_indices, sr=tr.meta.sampling_rate, hop_length=hop_length, n_fft=None)
        freqs = np.arange(0, 1 + n_fft / 2) * tr.meta.sampling_rate / n_fft

    time_abs = list([tr.stats.starttime + time_rel[0]])
    time_abs[0] = tr.stats.starttime + time_rel[0]
    for i in range(1, len(time_rel)):
        time_abs.append(tr.stats.starttime + time_rel[i])

    fig = px.imshow(S_db, x=time_abs, y=freqs, origin='lower', labels={'x': 'Time', 'y': 'Frequency (Hz)', 'color': 'Power (dB)'},
                    color_continuous_scale='jet', zmin=75, zmax=130)
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


global ST
ST = obspy.Stream([obspy.Trace(), obspy.Trace(), obspy.Trace()])
global channels
channels = ['X', 'Y', 'Z']


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
# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
dcc.Dropdown(['Geophone1','Geophone2','Geophone3','Geophone4','Geophone5','Geophone6','Geophone7','Geophone8'],id='geophone_selector', value=geophone),
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
    dcc.Graph(id='time_plot')
])


@app.callback(
    Output('time_plot', 'figure'),
    Input('channel_selector', 'value'),
    Input('startdate', 'value'),
    Input('enddate', 'value'),
    Input('geophone_selector', 'value')
)
def update(channel_selector, startdate, enddate, geo_sel):
    if ctx.triggered_id == 'geophone_selector':
        for j in range(0, 3):
            path = path_data + '_' + geo_sel + '_' + channels[j]
            print(path)
            tr = read_and_preprocessing(path, format_in, starttime, endtime)
            ST[j] = tr

        del tr

    if channel_selector == 'X':
        trace = ST[0]
    elif channel_selector == 'Y':
        trace = ST[1]
    else:
        trace = ST[2]

    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)

    fig1 = prepare_fig(trace=trace, start_time=start_time, end_time=end_time)
    print('Graph updated!')
    return fig1


# Main program

if __name__ == "__main__":
    app.run(debug=False)
    
