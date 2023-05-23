# Plot spectrograms per time intervals
# Description: script that reads datafiles of a specific location (geophone) and channel from a directory and computes
# a spectrogram per specified interval of time using librosa library. Spectrogram plots are saved in independent image
# files.

import os

import matplotlib.ticker
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator, AutoLocator, MaxNLocator)
from matplotlib.dates import AutoDateLocator, AutoDateFormatter
import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
import librosa
import numpy as np
from utils import read_data_from_folder
import argparse
import yaml
import pickle

"""
Functions
"""
def read_and_preprocessing(path_data, format_in, starttime, endtime):
    """
    Read, sort, merge, and filter data
    """
    # Read data
    print(f'Reading data ...')
    st = read_data_from_folder(path_data, format_in, starttime, endtime)
    print(f'Sample number per data file: {len(st[0].data)}')

    # Sort data
    print(f'Sorting data ...')
    st.sort(['starttime'])
    print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

    # Filtering 50 Hz
    if filter_50Hz_f:
        print(f'Filtering 50 Hz signal ...')
        for i_tr, tr in tqdm(enumerate(st)):
            st[i_tr].data = obspy.signal.filter.bandstop(tr.data, 49, 51, tr.meta.sampling_rate, corners=8,
                                                         zerophase=True)

    return st

def prepare_fig(tr, a_min, a_max, fig, ax):
    print(f'Preparing figure...')

    # Decimation
    """
    print(f'Decimation...')
    num_samples = len(tr.data)
    target_num_samples = 0.8 * fig.get_size_inches()[0] * fig.dpi  # Effective number of samples in the plot
    # More samples are considered than available in image resolution to allow zoom in vector format
    oversampling_factor = 100
    factor = int(num_samples / (target_num_samples * oversampling_factor))
    if factor > 1:
        tr.decimate(factor, no_filter=True)  # No antialiasing filtering because of lack of stability due to large decimation factor
    """
    """ Two lengthy
    fm = num_samples * 0.5
    target_fm = target_num_samples * 0.5
    corner_freq = 0.4 * target_num_samples  # [Hz] Note that Nyquist is 0.5 * target_fm
    if corner_freq < fm / 2:  # To avoid ValueError
        tr.filter('lowpass', freq=corner_freq, corners=10, zerophase=True)    
    tr.interpolate(sampling_rate=target_fm, method='lanczos', a=20)
    """

    fig.suptitle(f'{tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel} '
                 f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} '
                 f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
                 )

    """
    Time intensity plot
    """
    print(f'Time plotting...')
    ax[0].plot(tr.times(('matplotlib')), tr.data, 'k')
    ax[0].set(xlabel="Date",
              ylabel="Amplitude"
              )
    # ax[0].set(xlim=["2005-06-01", "2005-08-31"])

    # Define the date format
    """
    date_form_major = DateFormatter("%d-%b-%Y %H")
    ax[0].xaxis.set_major_formatter(date_form_major)
    date_form_minor = DateFormatter("%M")
    ax[0].xaxis.set_minor_formatter(date_form_minor)
    #ax[0].xaxis.set_major_locator(mdates.HourLocator())
    #ax[0].xaxis.set_minor_locator(mdates.MinuteLocator())
    locator = mdates.AutoDateLocator()
    ax[0].xaxis.set_major_locator(locator)
    #fig.autofmt_xdate()  # Angle date
    """

    # yaxis
    ax[0].yaxis.set_minor_locator(AutoMinorLocator())

    """
    # Change ticks
    ax[0].tick_params(axis='x', which='major', length=32, width=5, labelsize=18, rotation=0)
    ax[0].tick_params(axis='y', which='major', length=18, width=5)
    ax[0].tick_params(axis='both', which='minor', length=8, width=3, labelsize=10, rotation=0)
    """

    # Change font size
    # ax[0].title.set_fontsize(18)
    # ax[0].xaxis.label.set_fontsize(18)
    # ax[0].yaxis.label.set_fontsize(18)
    # map(lambda p: p.set_fontsize(18), ax[0].get_xticklabels())
    # map(lambda p: p.set_fontsize(18), ax[0].get_yticklabels())

    # Use the parameters [a_min, a_max] if data values are inside that range. If not use the min and max data
    # values.
    min_val, max_val = np.percentile(tr.data, [0, 100])
    if a_min <= min_val and a_max >= max_val:
        ax[0].set(ylim=[a_min, a_max])

    #ax[0].autoscale(enable=True, axis='x', tight=True)


    """
    Spectrogram plot
    """
    print(f'Spectrogram computation...')
    D = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
    # Time of STFT segments (for centered window)
    frame_indices = np.arange(D.shape[1])
    time_rel = librosa.frames_to_time(frame_indices, sr=tr.meta.sampling_rate, hop_length=hop_length, n_fft=None)
    #time_rel = librosa.frames_to_samples(D, hop_length=hop_length, n_fft=n_fft)
    #time_rel = np.arange(win_length/2, len(tr.data) - win_length/2 + 1, hop_length)/float(tr.meta.sampling_rate)
    time_abs = tr.stats.starttime.matplotlib_date + (time_rel / mdates.SEC_PER_DAY)
    # Spectrogram magnitudes to a decibel scale
    S_db = librosa.amplitude_to_db(np.abs(D), ref=1, amin=1e-5, top_db=None)
    img = librosa.display.specshow(S_db, cmap='jet', sr=tr.meta.sampling_rate, hop_length=hop_length, x_axis='time', y_axis='linear',
                                   ax=ax[1], vmin=S_min, vmax=S_max, x_coords=time_abs)
    ax[1].set(xlabel="Date",
              ylabel="Frequency"
              )
    # ax[1].set(xlim=["2005-06-01", "2005-08-31"])

    # Define the date format
    date_form_major = DateFormatter("%d-%b-%Y\n %H:%M")
    ax[1].xaxis.set_major_formatter(date_form_major)
    locator = AutoDateLocator(minticks=6,  maxticks=9, interval_multiples=False)
    locator.intervald['HOURLY'] = np.arange(12)+1
    locator.intervald['MINUTELY'] = np.arange(60)+1
    locator.intervald['SECONDLY'] = [1, 3, 5, 10, 15, 20, 30, 35, 40, 45, 50, 55]
    ax[1].xaxis.set_major_locator(locator)
    #ax[1].xaxis.set_major_locator(mdates.HourLocator())
    #date_form_minor = DateFormatter("%M")
    #ax[1].xaxis.set_minor_formatter(date_form_minor)
    #ax[1].xaxis.set_minor_locator(mdates.MinuteLocator())
    #locator = AutoDateLocator()
    #ax[1].xaxis.set_major_locator(locator)
    #ax[1].xaxis.set_minor_locator(locator)
    """
    locator = AutoDateLocator()
    formatter = AutoDateFormatter(locator)
    ax[1].xaxis.set_major_formatter(formatter)
    """

    #fig.autofmt_xdate()  # Angle date

    # Change ticks
    ax[1].tick_params(axis='x', which='major', length=6, width=2, labelsize=8, rotation=0)
    """
    ax[1].tick_params(axis='x', which='major', length=32, width=5, labelsize=18, rotation=0)
    ax[1].tick_params(axis='y', which='major', length=18, width=5)
    ax[1].tick_params(axis='both', which='minor', length=8, width=3, labelsize=10, rotation=0)
    """

    fig.colorbar(img, ax=ax, format="%+2.f dB")

    # To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
    for ax_i in ax:
        ax_i.label_outer()

    #ax[1].autoscale(enable=True, axis='x', tight=True)
    return fig, ax


def save_figure(path_output, prefix_name, tr, fig, fig_format):
    print(f'Saving figure...')
    plt.figure(fig)
    os.makedirs(path_output, exist_ok=True)
    file_name = f'{path_output}/{prefix_name}_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
                f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} ' \
                f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}.{fig_format}'
    """
    file_name_pickle = f'{path_output}/{prefix_name}_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
                f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} ' \
                f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}.pickle'
    pickle.dump(fig, open(file_name_pickle, 'wb'))
    """
    plt.savefig(f'{file_name}')


# Main program
if __name__ == "__main__":
    """
    Process input arguments given by the configuration file.
    The configuration file can have several set of parameters for plotting different geophones and channels.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conf_path")
    args = parser.parse_args()
    par_list = list()
    with open(args.conf_path, mode="rb") as file:
        for par in yaml.safe_load_all(file):
            par_list.append(par)

    """ 
    Process every set of parameters 
    """
    for i, par in enumerate(par_list):
        print(f'Processing parameter set {i + 1} out of {len(par_list)}')

        # Simplify variable names
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
        time_interval_one_row = par['day_plotting']['time_interval_one_row']
        fig_format = par['fig_format']
        verbose = par['verbose']

        # Date preprocessing
        if starttime:
            starttime = UTCDateTime(starttime)
        if endtime:
            endtime = UTCDateTime(endtime)

        """
        Read, sort, and filter data
        """
        st = read_and_preprocessing(path_data, format_in, starttime, endtime)

        """
        Plot spectrogram per period
        """
        print(f'Saving spectrograms every {spec_interval/3600} hours ...')
        # Group streams of data per user defined time period
        startday = UTCDateTime(st[0].stats.starttime.date)
        endday = UTCDateTime(st[-1].stats.endtime.date)
        for c, i in tqdm(enumerate(range(int(startday.timestamp), int(endday.timestamp), spec_interval))):
            st_cp = st.slice(UTCDateTime(i), UTCDateTime(i) + spec_interval)
            st_cp.sort(['starttime'])
            # Merge traces
            print(f'\nMerging data for the {c}th slot of {spec_interval/3600} hour ...')
            st_cp.merge(method=0, fill_value=0)
            tr = st_cp[0]

            # Prepare figure: spectrograms
            plt.rcParams['font.size'] = 18  # Change font size
            fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(19, 10), dpi=100)
            fig, ax = prepare_fig(tr, a_min, a_max, fig, ax)

            # Save figure
            save_figure(path_output, 'Spectrogram', tr, fig, fig_format)

            plt.close(fig)
            del tr
