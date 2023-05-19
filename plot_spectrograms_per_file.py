"""
Plot spectrogram per data file.

Script that reads datafiles of a specific location (geophone) and channel from a directory and computes a spectogram
per data file using librosa library. Spectrogram plots are saved in independent image files.
"""

import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator, AutoLocator, MaxNLocator)
import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
import librosa
from utils import read_data_from_folder
import numpy as np
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
    fig.suptitle(f'{tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel} '
                 f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} '
                 f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
                 )

    """
    Time intensity plot
    """
    ax[0].plot(tr.times(('matplotlib')), tr.data, 'k')
    ax[0].set(xlabel="Date",
              ylabel="Amplitude"
              )
    # ax[0].set(xlim=["2005-06-01", "2005-08-31"])

    # Define the date format
    date_form_major = DateFormatter("%d-%b-%Y")
    ax[0].xaxis.set_major_formatter(date_form_major)
    date_form_minor = DateFormatter("%H")
    ax[0].xaxis.set_minor_formatter(date_form_minor)
    ax[0].xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax[0].xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 4)))
    fig.autofmt_xdate()  # Angle date

    # yaxis
    ax[0].yaxis.set_minor_locator(AutoMinorLocator())

    # Change ticks
    ax[0].tick_params(axis='both', which='major', length=12, width=4)
    ax[0].tick_params(axis='x', which='major', labelsize=28)
    ax[0].tick_params(axis='both', which='minor', length=8, width=3)
    ax[0].tick_params(axis='x', which='minor', labelsize=18, rotation=25)

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

    """
    Spectrogram plot
    """
    D = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
    # Spectrogram magnitudes to a decibel scale
    S_db = librosa.amplitude_to_db(np.abs(D), ref=1, amin=1e-5, top_db=None)
    img = librosa.display.specshow(S_db, cmap='jet', sr=sr, hop_length=hop_length, x_axis='time', y_axis='linear',
                                   ax=ax[1], vmin=S_min, vmax=S_max)
    ax[1].set(xlabel="Date",
              ylabel="Frequency"
              )
    # ax[0].set(xlim=["2005-06-01", "2005-08-31"])

    # Define the date format
    date_form_major = DateFormatter("%d-%b-%Y")
    ax[1].xaxis.set_major_formatter(date_form_major)
    date_form_minor = DateFormatter("%H")
    ax[1].xaxis.set_minor_formatter(date_form_minor)
    ax[1].xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax[1].xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 4)))
    fig.autofmt_xdate()  # Angle date

    fig.colorbar(img, ax=ax, format="%+2.f dB")

    # To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
    for ax_i in ax:
        ax_i.label_outer()

    plt.tight_layout()
    return fig


def save_figure(path_output, tr, fig):
    print(f'Saving figure...')
    plt.figure(fig)
    os.makedirs(path_output, exist_ok=True)
    file_name = f'{path_output}/spectrogram_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
                f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} ' \
                f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}.png'
    """
    file_name_pickle = f'{path_output}/spectrogram_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
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
        a_max = par['plotting']['a_max']
        a_min = par['plotting']['a_min']
        S_max = par['plotting']['S_max']
        S_min = par['plotting']['S_min']
        time_interval_one_row = par['day_plotting']['time_interval_one_row']
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
        Plot spectrogram per data file
        """
        # Save a spectrogram plot per data file.
        print(f'Saving spectrograms per data file ...')
        for tr in tqdm(st):
            # Prepare figure: spectrograms
            plt.rcParams['font.size'] = 30  # Change font size
            fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(41, 23), dpi=100)
            fig = prepare_fig(tr, a_min, a_max, fig, ax)

            # Save figure
            save_figure(path_output, tr, fig)

            plt.close(fig)






