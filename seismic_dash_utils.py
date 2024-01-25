import obspy
from utils import read_data_from_folder
import obspy.signal.filter
import webbrowser
import pandas as pd
import plotly.express as px
from scipy.ndimage import uniform_filter1d
import numpy as np

def read_and_preprocessing(path, in_format, start, end, filter_50Hz_f):
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
        trace.data = obspy.signal.filter.bandstop(trace.data, 49, 51, trace.meta.sampling_rate, corners=8,
                                                  zerophase=True)

    return trace


def open_browser(port):
    webbrowser.open_new("http://localhost:{}".format(port))


def generate_title(tr, prefix_name):
    title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel}, from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
    return title


def prepare_time_plot(tr, oversampling_factor):
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
    ylabel = "Amplitude"
    title = generate_title(tr, prefix_name)

    fig = px.line(df, x="times", y="data", labels={'times': '', 'data': ylabel})
    fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
    fig['layout']['margin'] = {'t': 30, 'b': 30}
    fig['layout']['xaxis']['automargin'] = False
    fig['layout']['yaxis']['autorange'] = True
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
    rsam = uniform_filter1d(abs(tr.data), size=n_samples)
    df = pd.DataFrame({'data': rsam, 'times': tr.times('utcdatetime')})  # check for problems with date format
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

