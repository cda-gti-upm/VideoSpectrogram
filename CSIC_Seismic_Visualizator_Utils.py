import os
import sys

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
from ltsa.ltsa import seismicLTSA
import librosa.display
import pickle

def read_data_from_folder(path_data, format, starttime, endtime, filter_50Hz_f, verbose=True):
    """
        Reads all data files from directory. First reads the headers of all the files to check the start and end time
         and, if necessary, reads the data from the files. If no data is found for the specified dates, returns an empy
        obspy.Stream.

        The 50 Hz filter is applied individually to each file for memory reasons.
    """

    if starttime is None:
        starttime = UTCDateTime('1980-01-01')
    if endtime is None:
        endtime = UTCDateTime('2050-01-01')

    print(f'Reading data from {path_data} from {starttime} until {endtime}...')
    dirlist = sorted(os.listdir(path_data))
    if filter_50Hz_f:
        print('Filtering 50 Hz is activated...')
    first_file = True
    st = obspy.Stream()
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                if first_file:
                    st_head = obspy.read(file, format=format, headonly=True)
                    if (starttime <= st_head[0].stats.starttime <= endtime) or (starttime <= st_head[0].stats.endtime <= endtime) or (starttime >= st_head[0].stats.starttime and endtime <= st_head[0].stats.endtime):
                        st = obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                        if filter_50Hz_f:
                            st[0].data = obspy.signal.filter.bandstop(st[0].data, 49.8, 50.2, st[0].meta.sampling_rate, corners=8,
                                                      zerophase=True)
                        first_file = False
                else:
                    st_head = obspy.read(file, format=format, headonly=True)
                    if (starttime <= st_head[0].stats.starttime <= endtime) or (starttime <= st_head[0].stats.endtime <= endtime) or (starttime >= st_head[0].stats.starttime and endtime <= st_head[0].stats.endtime):
                        new_st = obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                        if filter_50Hz_f:
                            new_st[0].data = obspy.signal.filter.bandstop(new_st[0].data, 49.8, 50.2, new_st[0].meta.sampling_rate, corners=8,
                                                      zerophase=True)
                        st += new_st
            except Exception as e:
                if verbose:
                    print("Cannot read %s (%s: %s)" % (file, type(e).__name__, e))
                    if e is pickle.UnpicklingError:
                        print(f'There is a problem with the PICKLE file: {file}')
                    sys.exit()
    return st
def read_and_preprocessing(path, in_format, start, end, filter_50Hz_f):
    """
        Reads the data for the specified path, format, start and end time. The 50 Hz filter is to eliminate the
        interference of the electric lines. If it is set to True, reading the files will take more time.
        After reading the data, the files are merged into one obspy.Trace and then processed to eliminate not appropiate
        values.
        If no data is available, returns an empty obspy.Trace.
    """
    # Read data
    stream = read_data_from_folder(path, in_format, start, end, filter_50Hz_f)

    # Sort data
    print(f'Sorting data...')
    stream.sort(['starttime'])

    try:
        print(f'Data spans from {stream[0].stats.starttime} until {stream[-1].stats.endtime}')
        # Merge traces
        print(f'Merging data...')
        stream.merge(method=0, fill_value=0)
        trace = stream[0]
        del stream
        '''
        if filter_50Hz_f:
            print(f'Filtering 50 Hz...')
            trace.data = obspy.signal.filter.bandstop(trace.data, 49, 51, trace.meta.sampling_rate, corners=8,
                                                      zerophase=True)
        '''
        #  Correct data anomalies
        print('Correcting data anomalies...')
        trace = correct_data_anomalies(trace)

    except Exception as e:
        print(f'Error reading data or no data is available for selected parameters: {e}')
        trace = obspy.Trace()

    return trace


def get_start_end_time(path, format='PICKLE'):
    """
        Returns the earliest start time and latest end time of all the PICKLE files in the path. Needed for the 3
        channel plot implementation, if a channel of one geophone do not have complete data for a time interval.
    """
    print(f'Checking start and end time of available data in {path}...')
    dirlist = sorted(os.listdir(path))
    starttime = []
    endtime = []

    for file in tqdm(dirlist):
        try:
            file = os.path.join(path, file)
            st_head = obspy.read(file, format=format, headonly=True)
            starttime.append(st_head[0].stats.starttime)
            endtime.append(st_head[0].stats.endtime)
        except Exception as e:
            print("Cannot read %s (%s: %s)" % (file, type(e).__name__, e))
            if e is pickle.UnpicklingError:
                print(f'There is a problem with the PICKLE file: {file}')
            sys.exit()
    return min(starttime), max(endtime)


def open_browser(port):
    """
        Opens the browser automatically
    """
    webbrowser.open_new("http://localhost:{}".format(port))


def generate_title(tr, prefix_name):
    """
        Generate title of the plot
    """
    title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel}, from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
    return title


def prepare_time_plot(tr, oversampling_factor):
    """
        Generates the amplitude plot. If the trace has too many samples it is split into windows and the maximum abs
        value is selected for each of them.
    """
    if len(tr) != 0:
        print(f'Preparing figure...')
        num_samples = len(tr.data)
        prefix_name = 'Seismic amplitude'
        print(f'{prefix_name} trace has {len(tr.data)} samples...')
        target_num_samples = 1920  # Resolution of the screen
        factor = int(num_samples / (target_num_samples * oversampling_factor))
        if factor > 1:

            df = max_per_window(tr, factor)
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
        fig.update_xaxes(
            showgrid=True,
            ticks="inside",
            tickson="boundaries",
            ticklen=10
        )
    else:
        fig = px.line()  # If the trace has no data generate an empty fig
    return fig


def get_3_channel_figures(starttime, endtime, geophone, filter_50Hz_f, path_root, oversampling_factor, format_in):
    channels = ['X', 'Y', 'Z']
    data_path = []
    start_times = []
    end_times = []

    for i in range(0, 3):
        data_path.append(path_root + '_' + geophone + '_' + channels[i])
        [start_files, end_files] = get_start_end_time(data_path[i])
        start_times.append(start_files)
        end_times.append(end_files)

    if starttime is None:
        starttime = max(start_times)
    else:
        start_times.append(starttime)
        starttime = max(start_times)

    if endtime is None:
        endtime = min(end_times)
    else:
        end_times.append(endtime)
        endtime = min(end_times)

    if starttime > endtime:
        print('Dates are invalid. Choose valid dates and press "Update data".')
        endtime = starttime
    tr = read_and_preprocessing(data_path[0], format_in, starttime, endtime, filter_50Hz_f)
    fig1 = prepare_time_plot_3_channels(tr, oversampling_factor, 'X')

    tr = read_and_preprocessing(data_path[1], format_in, starttime, endtime, filter_50Hz_f)
    fig2 = prepare_time_plot_3_channels(tr, oversampling_factor, 'Y')

    tr = read_and_preprocessing(data_path[2], format_in, starttime, endtime, filter_50Hz_f)
    fig3 = prepare_time_plot_3_channels(tr, oversampling_factor, 'Z')

    return fig1, fig2, fig3, fig1['data'][0]['x'][0], fig1['data'][0]['x'][-1]

def prepare_time_plot_3_channels(tr, oversampling_factor, channel):
    print(f'Preparing figure...')
    num_samples = len(tr.data)
    prefix_name = 'Seismic amplitude'
    print(f'{prefix_name} trace has {len(tr.data)} samples...')
    target_num_samples = 1920
    factor = int(num_samples / (target_num_samples * oversampling_factor))
    if factor > 1:
        df = max_per_window(tr, factor)
        print(f'{prefix_name} trace reduced to {len(df["data"])} samples...')
        '''
        tr.decimate(factor, no_filter=True) #tr.decimate necesita que se haga copy() antes para consercar los datos
        print(f'{prefix_name} trace reduced to {len(tr.data)} samples...')
        '''
    else:
        df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})  # check for problems with date format

    # Plotting and formatting
    print(f'Plotting and formating {prefix_name}...')
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
    fig.update_xaxes(
        showgrid=True,
        ticks="inside",
        tickson="boundaries",
        ticklen=10
    )
    return fig


def prepare_rsam(tr):
    n_samples = int(tr.meta.sampling_rate * 60 * 10)  # Amount to 10 minutes
    print('Computing RSAM...')
    tr.data = uniform_filter1d(abs(tr.data), size=n_samples)
    df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})  # check for problems with date format
    xlabel = "Date"
    ylabel = "Amplitude"
    title = generate_title(tr, 'RSAM')
    fig = px.line(df, x="times", y="data", labels={'times': '', 'data': ylabel})
    fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
    fig['layout']['margin'] = {'t': 30, 'b': 30}
    fig['layout']['xaxis']['automargin'] = False
    fig['layout']['yaxis']['autorange'] = True
    fig.update_xaxes(
        showgrid=True,
        ticks="inside",
        tickson="boundaries",
        ticklen=10
    )
    return fig


def prepare_spectrogram(tr, s_min, s_max, hop_length, win_length, n_fft, window):

    """
        Computation of the spectrogram and generation of the figure. If the number of samples of the spectrogram is
        greater than 100 times the horizontal resolution of the screen (default 1920), the LTSA is computed. If not, a
        standard spectrogram.
    """
    res = 1920
    num_samples = math.ceil(len(tr.data) / hop_length)
    if num_samples > (res * 10):
        print('Computing LTSA...')
        d = seismicLTSA(tr.data, tr.meta.sampling_rate)
        params = {'div_len': int(np.round(len(tr.data) / res)),  # Length in numer of samples
                  'subdiv_len': win_length,
                  'nfft': n_fft,
                  'noverlap': hop_length}
        d.set_params(params)

        # compute the LTSA -- identical to s.compute()
        d.compute(ref=1, amin=1e-5, top_db=None)
        S_db = d.ltsa
        frame_indices = np.arange(S_db.shape[1])
        time_rel = (np.asanyarray(frame_indices) * d.div_len + (d.div_len / 2)).astype(int) / float(
            tr.meta.sampling_rate)
        freqs = np.arange(0, n_fft / 2) * tr.meta.sampling_rate / n_fft

    else:
        print('Computing standard spectrogram...')
        d = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)

        S_db = librosa.amplitude_to_db(np.abs(d), ref=1, amin=1e-5, top_db=None)
        frame_indices = np.arange(d.shape[1])
        time_rel = librosa.frames_to_time(frame_indices, sr=tr.meta.sampling_rate, hop_length=hop_length, n_fft=None)
        freqs = np.arange(0, 1 + n_fft / 2) * tr.meta.sampling_rate / n_fft

    time_abs = list([tr.stats.starttime + time_rel[0]])
    time_abs[0] = tr.stats.starttime + time_rel[0]
    for i in range(1, len(time_rel)):
        time_abs.append(tr.stats.starttime + time_rel[i])
    title = generate_title(tr, 'Spectrogram')
    fig = px.imshow(S_db, x=time_abs, y=freqs, origin='lower',
                    labels={'y': 'Frequency (Hz)', 'color': 'Power (dB)'},
                    color_continuous_scale='jet', zmin=s_min, zmax=s_max)

    fig.layout['coloraxis']['colorbar']['orientation'] = 'h'
    fig.layout['coloraxis']['colorbar']['yanchor'] = 'bottom'
    fig.layout['coloraxis']['colorbar']['y'] = -0.25
    fig['layout']['yaxis']['autorange'] = False
    fig['layout']['yaxis']['range'] = [5, 125]
    fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
    fig['layout']['margin'] = {'t': 30, 'b': 30}
    fig['layout']['xaxis']['automargin'] = False
    fig.update_xaxes(
        showgrid=True,
        ticks="inside",
        tickson="boundaries",
        ticklen=10
    )

    return fig


def update_layout(layout, min_y, max_y, auto_y, fig):
    """
        Updates the layout of the amplitude plot. If autorange is selected in the app, the maximum amplitude is set to
        (+-)100.000.
    """
    if auto_y == ['autorange']:
        tr_max = np.max(fig['data'][0]['y'])
        tr_min = np.min(fig['data'][0]['y'])
        max_allowed = 100000
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


def update_layout_3_channels(fig, starttime, endtime, min_y, max_y, auto_y):
    """
        Manages the amplitude of the plots in the 3 channel implementation. As the traces are not available in memory,
        when the data is sliced the autorange does not work. We need to compute manually the maximum and minimum value
        of the data contained in the figure for the selected start and end time and then generate the appropiate y-axis
        for each channel.
    """

    layout = fig['layout']
    fig['layout']['xaxis']['autorange'] = False
    fig['layout']['xaxis']['range'] = [starttime, endtime]
    if auto_y == ['autorange']:
        times = np.array(fig['data'][0]['x'])
        data = np.array(fig['data'][0]['y'])
        displayed_data = data[(times > starttime) & (times < endtime)]
        max_fig = np.max(displayed_data)
        min_fig = np.min(displayed_data)
        layout['yaxis']['autorange'] = False
        layout['yaxis']['range'] = [min_fig + 0.1 * min_fig, max_fig + 0.1 * max_fig]
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
    abs_th = 500000
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
    """
        Puts to 0 all the samples that have an absolute value greater than 500.000, an inf value or a NaN value.
    """

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


def max_per_window(tr, factor):
    """
        As the trace has many samples, but not all can be fitted on the screen, a new trace is generated with fewer
        samples. The best approach we found was to split the trace into slices and for each of them keep the sample that
        has the maximum absolute value. By doing this, we guarantee that seismic activity is not missed. Then, if the
        wishes to have a more precise representation the trace will be recalculated after the zoom.
    """
    length = len(tr)
    n_intervals = math.ceil(length / factor)
    interval_length = factor
    data = np.arange(0., n_intervals)

    for i in range(0, n_intervals):
        max_value = 0
        for j in range(i * interval_length, i * interval_length + interval_length):
            if j >= length:
                break
            if abs(tr.data[j]) > abs(max_value):
                max_value = tr.data[j]

        data[i] = max_value

    tr.decimate(factor, no_filter=True)
    tr.data = data
    df = pd.DataFrame({'data': data, 'times': tr.times('utcdatetime')})
    return df


def create_config(params, file_name):
    # Step 1: Import Pickle
    import pickle

    # Step 2: Saving Variables

    if not os.path.exists("./user_config"):
        os.mkdir("./user_config")
    file_path = f"./user_config/{file_name}.pickle"
    # Open the file in binary mode
    with open(file_path, 'wb') as file:
        # Serialize and write the variable to the file
        pickle.dump(params, file, protocol=pickle.HIGHEST_PROTOCOL)


def load_config(file_path):
    loaded_data = None
    try:
        with open(file_path, 'rb') as file:
            # Deserialize and retrieve the variable from the file
            loaded_data = pickle.load(file)
    except Exception as e:
        print("Cannot read %s (%s: %s)" % (file, type(e).__name__, e))

    return loaded_data
