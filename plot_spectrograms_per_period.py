# Plot spectrograms per time intervals
# Description: script that reads datafiles of a specific location (geophone) and channel from a directory and computes
# a spectrogram per specified interval of time using librosa library. Spectrogram plots are saved in independent image
# files.

import os

import matplotlib.ticker
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator, AutoLocator, MaxNLocator)
import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
import librosa
import numpy as np
from utils import read_data_from_folder


# Parameters -----------------------------------------------------------------------------------------------------------
# Path to input datafiles regarding a specific location (geophone) and channel
path_data = './data/LDF/CSIC/LaPalma/Geophone_0/X/'  # './data/prueba'
# Path for output plots
base_path_output = './data/spectrograms'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". Alternative format using a ISO8601:2004 string:
                  # "2009-12-31T12:23:34.5"
endtime = None
# Spectrogram interval in seconds
spectrogram_interv = 30 * 60
verbose = True
# Spectrogram parameters (see function librosa.stft)
win_length = 1024
hop_length = win_length // 16
n_fft = 4096
window = 'hann'
sr = 250
# Maximum and minimum power spectral values and time amplitude to represent spectrograms and time plots. Use
# 'range_espectrograms.py' to infer such as # values.
S_max = 130 # 145
S_min = 75  # 75
a_max = 40000
a_min = -40000
# Flag to filter 50 Hz
filter_50Hz = True

# Internal parameters
# Format of input datafiles
format_in = 'PICKLE'


if __name__ == "__main__":
    # Date preprocessing
    if starttime:
        starttime = UTCDateTime(starttime)
    if endtime:
        endtime = UTCDateTime(endtime)

    # Read data
    print(f'Reading data files ...')
    st = read_data_from_folder(path_data, format_in, starttime, endtime)
    print(f'Sample number per data file: {len(st[0].data)}')

    # Sort data
    print(f'Sorting data ...')
    st.sort(['starttime'])
    print(f'Data spans from {st[0].stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")} until {st[-1].stats.endtime.strftime("%d-%b-%Y at %H:%M:%S")}')

    # Save spectrogram and time plots in independent image files according to specify time length.
    print(f'Saving spectrograms every {spectrogram_interv/3600} hours ...')
    # Group streams of data per user defined time period
    startday = UTCDateTime(st[0].stats.starttime.date)
    endday = UTCDateTime(st[-1].stats.endtime.date)
    last_time = []
    for c, i in tqdm(enumerate(range(int(startday.timestamp), int(endday.timestamp), spectrogram_interv))):
        st_cp = st.copy()
        st_cp = st_cp.slice(UTCDateTime(i), UTCDateTime(i) + spectrogram_interv)
        st_cp.sort(['starttime'])
        # Merge traces
        print(f'\nMerging data for the {c}th slot of {spectrogram_interv/3600} hour ...')
        st_cp.merge(method=0, fill_value=0)
        tr = st_cp[0]

        # Filtering 50 Hz
        if filter_50Hz:
            tr.data = obspy.signal.filter.bandstop(tr.data, 49, 51, sr, corners=8, zerophase=True)

        # Generate time and spectrograms plots
        fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(20, 10), dpi=100)
        t0 = tr.stats.starttime
        fig.suptitle(f'From {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")} until {tr.stats.endtime.strftime("%d-%b-%y at %H:%M:%S")} \n'
                     f'{tr.meta.location} \n Channel: {tr.meta.channel}')

        # Time intensity plot
        ax[0].plot(tr.times(reftime=t0), tr.data, 'k')
        ax[0].set_xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
        ax[0].set_ylabel('Intensity')
        # Use the parameters [a_min, a_max] if data values are inside that range, if not use the min and max data values.
        min_val, max_val = np.percentile(tr.data, [0, 100])
        if a_min <= min_val and a_max >= max_val:
            ax[0].set_ylim([a_min, a_max])

        # Spectrogram plot
        print(f'Computing spectrogram for the {c}th slot of {spectrogram_interv/3600} hour ...')
        D = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
        # Spectrogram magnitudes to a decibel scale
        S_db = librosa.amplitude_to_db(np.abs(D), ref=1, amin=1e-5, top_db=None)
        img = librosa.display.specshow(S_db, cmap='jet', sr=sr, hop_length=hop_length, x_axis='time', y_axis='linear',
                                       ax=ax[1], vmin=S_min, vmax=S_max)
        #ax[1].set(title=f'Seconds relative to {t0}')
        ax[1].set_xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
        ax[1].xaxis.set_major_locator(MaxNLocator(15))
        ax[1].xaxis.set_minor_locator(MaxNLocator(60))
        fig.colorbar(img, ax=ax, format="%+2.f dB")

        # To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
        for ax_i in ax:
            ax_i.label_outer()

        os.makedirs(base_path_output + '/spectrograms_per_period', exist_ok=True)
        plt.savefig(f'{base_path_output}/spectrograms_per_period/{tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")}.png')
        plt.close()

        last_time = i+spectrogram_interv

    # Save last spectrogram and time plots (incomplete interval)
    if (last_time + 1) < int(endday.timestamp):
        st_cp = st.copy()
        st_cp = st_cp.slice(UTCDateTime(last_time + 1), endday.timestamp)
        st_cp.sort(['starttime'])
        # Merge traces
        print(f'\nMerging data for the {c}th slot of {spectrogram_interv / 3600} hour ...')
        st_cp.merge(method=0, fill_value=0)
        tr = st_cp[0]

        # Filtering 50 Hz
        if filter_50Hz:
            tr.data = obspy.signal.filter.bandstop(tr.data, 49, 51, sr, corners=8, zerophase=True)

        # Generate time and spectrograms plots
        fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(20, 10), dpi=100)
        t0 = tr.stats.starttime
        fig.suptitle(
            f'From {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")} until {tr.stats.endtime.strftime("%d-%b-%y at %H:%M:%S")} \n'
            f'{tr.meta.location} \n Channel: {tr.meta.channel}')

        # Time intensity plot
        ax[0].plot(tr.times(reftime=t0), tr.data, 'k')
        ax[0].set_xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
        ax[0].set_ylabel('Intensity')
        # Use the parameters [a_min, a_max] if data values are inside that range, if not use the min and max data values.
        min_val, max_val = np.percentile(tr.data, [0, 100])
        if a_min <= min_val and a_max >= max_val:
            ax[0].set_ylim([a_min, a_max])

        # Spectrogram plot
        print(f'Computing spectrogram for the {c}th slot of {spectrogram_interv / 3600} hour ...')
        D = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
        # Spectrogram magnitudes to a decibel scale
        S_db = librosa.amplitude_to_db(np.abs(D), ref=1, amin=1e-5, top_db=None)
        img = librosa.display.specshow(S_db, cmap='jet', sr=sr, hop_length=hop_length, x_axis='time', y_axis='linear',
                                       ax=ax[1], vmin=S_min, vmax=S_max)
        # ax[1].set(title=f'Seconds relative to {t0}')
        ax[1].set_xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
        ax[1].xaxis.set_major_locator(MaxNLocator(15))
        ax[1].xaxis.set_minor_locator(MaxNLocator(60))
        fig.colorbar(img, ax=ax, format="%+2.f dB")

        # To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
        for ax_i in ax:
            ax_i.label_outer()

        os.makedirs(base_path_output + '/spectrograms_per_period', exist_ok=True)
        plt.savefig(
            f'{base_path_output}/spectrograms_per_period/{tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")}.png')
        plt.close()

