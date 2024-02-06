import os
import time
from obspy.core import UTCDateTime
import obspy.signal.filter
import webbrowser
import pandas as pd
import plotly.express as px
from scipy.ndimage import uniform_filter1d
import obspy
import numpy as np
from tqdm import tqdm
import math


def read_data_from_folder(path_data, format, starttime, endtime, filter_50Hz_f, verbose=True):
    # Read all data files from directory
    if starttime is None:
        starttime = UTCDateTime('1980-01-01')
    if endtime is None:
        endtime = UTCDateTime('2050-01-01')

    print(f'Reading from {starttime} to {endtime}')
    dirlist = sorted(os.listdir(path_data))
    if filter_50Hz_f:
        print('Reading and filtering 50 Hz ...')
    first_file = True
    st = obspy.Stream()
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                if first_file:
                    st_head = obspy.read(file, format=format, headonly=True)
                    if (starttime <= st_head[0].stats.starttime <= endtime) or (starttime <= st_head[0].stats.endtime <= endtime):
                        st = obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                        if filter_50Hz_f:
                            st[0].data = obspy.signal.filter.bandstop(st[0].data, 49, 51, st[0].meta.sampling_rate, corners=8,
                                                      zerophase=True)
                        first_file = False
                else:
                    st_head = obspy.read(file, format=format, headonly=True)
                    if (starttime <= st_head[0].stats.starttime <= endtime) or (starttime <= st_head[0].stats.endtime <= endtime):
                        new_st = obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                        if filter_50Hz_f:
                            new_st[0].data = obspy.signal.filter.bandstop(new_st[0].data, 49, 51, new_st[0].meta.sampling_rate, corners=8,
                                                      zerophase=True)
                        st += new_st
            except Exception as e:
                if verbose:
                    print("Cannot read %s (%s: %s)" % (file, type(e).__name__, e))
    return st
def read_and_preprocessing(path, in_format, start, end, filter_50Hz_f):
    # Read data
    print(f'Reading data ...')
    stream = read_data_from_folder(path, in_format, start, end, filter_50Hz_f)

    # Sort data
    print(f'Sorting data ...')
    stream.sort(['starttime'])
    try:
        print(f'Data spans from {stream[0].stats.starttime} until {stream[-1].stats.endtime}')

        # Merge traces
        print(f'Merging data ...')
        stream.merge(method=0, fill_value=0)
        trace = stream[0]
        del stream
        '''
        if filter_50Hz_f:
            print(f'Filtering 50 Hz ...')
            trace.data = obspy.signal.filter.bandstop(trace.data, 49, 51, trace.meta.sampling_rate, corners=8,
                                                      zerophase=True)
        '''
        trace = correct_data_anomalies(trace)
    except Exception as e:
        print('Error reading data')
        trace = obspy.Trace()

    return trace


def get_start_end_time(path, format='PICKLE'):
    dirlist = sorted(os.listdir(path))
    starttime = []
    endtime = []
    for file in tqdm(dirlist):
        file = os.path.join(path, file)
        st_head = obspy.read(file, format=format, headonly=True)
        starttime.append(st_head[0].stats.starttime)
        endtime.append(st_head[0].stats.endtime)

    return min(starttime), max(endtime)


def open_browser(port):
    webbrowser.open_new("http://localhost:{}".format(port))


def generate_title(tr, prefix_name):
    title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel}, from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
    return title


def prepare_time_plot(tr, oversampling_factor):
    if len(tr) != 0:
        print(f'Preparing figure...')
        print('Updating dates...')
        # Decimation
        print(f'Decimation...')
        num_samples = len(tr.data)
        prefix_name = 'Seismic amplitude'
        print(f'{prefix_name} trace has {len(tr.data)} samples...')
        target_num_samples = 1920
        factor = int(num_samples / (target_num_samples * oversampling_factor))
        if factor > 1:

            df = av_signal(tr, factor)
            print(f'{prefix_name} trace reduced to {len(df["data"])} samples...')
            """
            tr.decimate(factor, no_filter=True)  # tr.decimate necesita que se haga copy() antes para consercar los datos
            print(f'{prefix_name} trace reduced to {len(tr.data)} samples...')
            df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})
            """
        else:
            df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})  # check for problems with date format

        # Plotting and formatting
        print(f'Plotting and formating {prefix_name}...')
        xlabel = "Date"
        ylabel = "Amplitude"
        title = generate_title(tr, prefix_name)

        fig = px.line(df, x="times", y="data", labels={'times': '', 'data': ylabel})
        fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
        fig['layout']['margin'] = {'t': 30, 'b': 30}
        fig['layout']['xaxis']['automargin'] = False
        fig['layout']['yaxis']['autorange'] = True
    else:
        fig = px.line()
    return fig


def prepare_time_plot_3_channels(tr, oversampling_factor, channel):
    print(f'Preparing figure...')
    print('Updating dates...')
    # Decimation
    print(f'Decimation...')
    num_samples = len(tr.data)
    prefix_name = 'Seismic amplitude'
    print(f'{prefix_name} trace has {len(tr.data)} samples...')
    target_num_samples = 1920
    factor = int(num_samples / (target_num_samples * oversampling_factor))
    if factor > 1:
        tr.decimate(factor, no_filter=True) #tr.decimate necesita que se haga copy() antes para consercar los datos
        print(f'{prefix_name} trace reduced to {len(tr.data)} samples...')

    # Plotting and formatting
    print(f'Plotting and formating {prefix_name}...')


    df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})  # check for problems with date format

    xlabel = "Date"
    ylabel = f"Amplitude {channel}"
    fig = px.line(df, x="times", y="data", labels={'times': '', 'data': ylabel})
    prefix_name = 'Seismic amplitude'
    if channel == 'X':
        title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, all channels, from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
        fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
        fig['layout']['margin'] = {'t': 30, 'b': 15}
    else:
        fig['layout']['margin'] = {'t': 15, 'b': 15}

    fig['layout']['xaxis']['automargin'] = False
    fig['layout']['yaxis']['autorange'] = True
    return fig


def prepare_rsam(tr):
    n_samples = int(tr.meta.sampling_rate * 60 * 10)  # Amount to 10 minutes
    tr.data = uniform_filter1d(abs(tr.data), size=n_samples)
    df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})  # check for problems with date format
    xlabel = "Date"
    ylabel = "Amplitude"
    title = generate_title(tr, 'RSAM')
    fig = px.line(df, x="times", y="data", labels={'data': ylabel})
    fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
    fig['layout']['margin'] = {'t': 30, 'b': 30}
    fig['layout']['xaxis']['automargin'] = False
    fig['layout']['yaxis']['autorange'] = True
    return fig


def update_layout(layout, min_y, max_y, auto_y, fig):
    if auto_y == ['autorange']:
        tr_max = np.max(fig['data'][0]['y'])
        tr_min = np.min(fig['data'][0]['y'])
        max_allowed = 433438
        if tr_max > max_allowed and tr_min > -max_allowed:
            layout['yaxis']['autorange'] = False
            layout['yaxis']['range'] = [tr_min, max_allowed]
        elif tr_max < max_allowed and tr_min < -max_allowed:
            layout['yaxis']['autorange'] = False
            layout['yaxis']['range'] = [-max_allowed, tr_max]
        elif tr_max > max_allowed and tr_min < -max_allowed:
            layout['yaxis']['autorange'] = False
            layout['yaxis']['range'] = [-max_allowed, max_allowed]
        else:
            layout['yaxis']['autorange'] = True

    else:
        layout['yaxis']['autorange'] = False
        layout['yaxis']['range'] = [min_y, max_y]
    return layout


def update_layout_rsam(layout, min_y, max_y, auto_y):
    if (auto_y == ['autorange']) or (min_y is None) or (max_y is None):
        layout['yaxis']['autorange'] = True

    else:
        layout['yaxis']['autorange'] = False
        layout['yaxis']['range'] = [min_y, max_y]

    return layout


def detect_anomalies(stream):
    abs_th = 433000
    # Detection of anomalous values
    for i, tr in enumerate(tqdm(stream)):
        # Detection of not-a-number values
        indnan = np.isnan(tr.data)
        if any(indnan):
            print(f'List of indexes containing a not-a-number value (NaN) in Trace {i}:')
            print(f'Indexes: {np.where(indnan)}')
        """
        else:
            print(f'Trace {i} does not contain not-a-number values (NaN)')
        """

        # Detection of infinite values
        indinf = np.isinf(tr.data)
        if any(indinf):
            print(f'List of indexes containing a infinite value (inf) in Trace {i}:')
            print(f'Indexes: {np.where(indinf)}')
        """
        else:
            print(f'Trace {i} does not contain infinite values (inf)')
        """

        # Detection of very large values
        indlarge = abs(tr.data) > abs_th
        if any(indlarge):
            print(f'Indexes: {np.where(indlarge)}')
            print(f'Values: {tr.data[indlarge]}')
        """
        else:
            print(f'Trace {i} does not contain large values')
        """


def correct_data_anomalies(tr):
    # Correction of anomalous values

    abs_th = 500000
    # Correction of not-a-number values
    indnan = np.isnan(tr.data)
    tr.data[indnan] = 0

    # Correction of infinite values
    indinf = np.isinf(tr.data)
    tr.data[indinf] = 0

    # Correction of very large values
    indlarge = abs(tr.data) > abs_th
    tr.data[indlarge] = 0

    return tr

def av_signal(tr, factor):
    length = len(tr)
    n_intervals = math.ceil(length / factor)
    interval_length = factor
    data = np.arange(0., n_intervals)

    for i in range(0, n_intervals):
        max_value = 0
        for j in range(i * interval_length, i * interval_length + interval_length):
            if j >= length:
                break
            if abs(tr.data[j]) > max_value:
                max_value = tr.data[j]

        data[i] = max_value

    tr.decimate(factor, no_filter=True)
    df = pd.DataFrame({'data': data, 'times': tr.times('utcdatetime')})  # check for problems with date format
    return df
"""
tr = obspy.Trace(np.arange(50))
df = av_signal(tr,8)
print(df['data'])
print(len(df['data']))



path_data = './data/CSIC_LaPalma_Geophone1_X'
format = 'PICKLE'
starttime = UTCDateTime('2021-10-01')
endtime = UTCDateTime('2021-10-03')

st = read_data_from_folder(path_data,format,starttime, endtime)
"""

