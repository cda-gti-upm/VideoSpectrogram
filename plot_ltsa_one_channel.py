"""
Plot LTSA (Long Term Spectral Average): one spectrogram plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent spectrogram plot for every
one.
"""

import os
import librosa.display
from tqdm import tqdm
import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator, AutoLocator, MaxNLocator)
from matplotlib.dates import DateFormatter
from matplotlib.dates import AutoDateLocator, AutoDateFormatter
from utils import read_data_from_folder
import numpy as np
import argparse
import yaml
import pickle
from scipy.ndimage import uniform_filter1d
from matplotlib.pyplot import show, colorbar
from ltsa.ltsa import seismicLTSA

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

    # Sort data
    print(f'Sorting data ...')
    st.sort(['starttime'])
    print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

    # Merge traces
    print(f'Merging data ...')
    st.merge(method=0, fill_value=0)
    tr = st[0]

    # Filtering 50 Hz
    if filter_50Hz_f:
        print(f'Filtering 50 Hz signal ...')
        tr.data = obspy.signal.filter.bandstop(tr.data, 49.8, 50.2, tr.meta.sampling_rate, corners=8, zerophase=True)

    return tr

def prepare_fig(tr, a_min, a_max, lf, hf, fig, ax):
    print(f'Preparing figure...')

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
    s = seismicLTSA(tr.data, tr.meta.sampling_rate)
    # Set and apply the parameters
    fig_size = fig.get_size_inches()*fig.dpi  # size in pixels
    params = {'div_len': int(np.round(tr.data.size/fig_size[0] * 10/9)),  # Length in numer of samples
              'subdiv_len': win_length,
              'nfft': n_fft,
              'noverlap': hop_length}
    s.set_params(params)

    # compute the LTSA -- identical to s.compute()
    s.compute(ref=1, amin=1e-5, top_db=None)

    S_db = s.ltsa
    # Time of STFT segments (for centered window)
    # The date tick per division is set at the middle of the interval division, instead of the beginning.
    frame_indices = np.arange(S_db.shape[1])
    time_rel = (np.asanyarray(frame_indices) * s.div_len + (s.div_len/2)).astype(int) / float(tr.meta.sampling_rate)
    time_abs = tr.stats.starttime.matplotlib_date + (time_rel / mdates.SEC_PER_DAY)
    # Spectrogram magnitudes to a decibel scale
    img = librosa.display.specshow(S_db, cmap='jet', sr=tr.meta.sampling_rate, hop_length=hop_length, x_axis='time', y_axis='linear',
                                   ax=ax[1], vmin=S_min, vmax=S_max, x_coords=time_abs)
    ax[1].set(xlabel="Date", ylabel="Frequency [Hz]")
    ax[1].set(ylim=[lf, hf])
    # ax[1].set(xlim=["2005-06-01", "2005-08-31"])

    # Define the date format
    # date_form_major = DateFormatter("%d-%b-%Y\n %H:%M")
    date_form_major = DateFormatter("%Y\n%d-%b\n %H:%M")
    ax[1].xaxis.set_major_formatter(date_form_major)
    locator = AutoDateLocator(minticks=6,  maxticks=12, interval_multiples=False)
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
    file_name_pickle = f'{path_output}/plot_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
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
        print(f'Processing parameter set {i+1} out of {len(par_list)}')

        # Simplify variable names
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
        Img_width = par['Img_width']
        Img_height = par['Img_height']
        verbose = par['verbose']

        win_length = par['spectrogram']['win_length']
        hop_length = par['spectrogram']['hop_length']
        n_fft = par['spectrogram']['n_fft']
        window = par['spectrogram']['window']
        S_max = par['plotting']['S_max']
        S_min = par['plotting']['S_min']
        Low_frequency = par['plotting']['Low_frequency']
        High_frequency = par['plotting']['High_frequency']

        # Date preprocessing
        if starttime:
            starttime = UTCDateTime(starttime)
        if endtime:
            endtime = UTCDateTime(endtime)

        """
        Read, sort, merge, and filter data
        """
        tr = read_and_preprocessing(path_data, format_in, starttime, endtime)
        #tr_rsam = tr.copy()

        """
        Plot LTSA
        """
        """
        s = seismicLTSA(tr.data, sampling_rate)
        # apply the parameters
        s.set_params(params)

        # compute the LTSA -- identical to s.compute()
        s.compute()
        """

        """
        # throw out data over 6kHz as there isn't much interesting activity there
        # in a typical song
        # s.crop(fmax=6000)
        s.show()

        colorbar()
        show()
        sys.exit()
        """
        # Prepare figure: spectrograms
        plt.rcParams['font.size'] = 18  # Change font size
        dpi = 100
        figsize = (round(Img_width/dpi), round(Img_height/dpi))
        fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=figsize, dpi=dpi)
        #fig, ax = plt.subplots(nrows=2, ncols=1, sharex=False, figsize=(19, 10), dpi=100)
        fig, ax = prepare_fig(tr, a_min, a_max, Low_frequency, High_frequency, fig, ax)

        # Save figure
        save_figure(path_output, 'LTSA', tr, fig, fig_format)

