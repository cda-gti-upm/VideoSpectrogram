# Script that reads datafiles of a specific location (geophone) and channel from a directory and computes a spectrogram
# per specified interval of time using librosa library. Spectrogram plots are saved in independent image files.

import os
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import obspy
from obspy.core import UTCDateTime
import librosa
import numpy as np


# Parameters -----------------------------------------------------------------------------------------------------------
# Path to input datafiles regarding a specific location (geophone) and channel
path_data = './data/CSIC/LaPalma/Geophone_0/X/'  # './data/prueba'
# Path for output plots
base_path_output = './data/spectrograms'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". Alternative format using a ISO8601:2004 string:
                  # "2009-12-31T12:23:34.5"
endtime = None
# Spectrogram interval in seconds
spectrogram_interv = 30 * 60
verbose = True


# Internal parameters
# Format of input datafiles
format_in = 'PICKLE'


def read_data_from_folder(path_data, format, starttime, endtime):
    # Read all data files from directory
    dirlist = sorted(os.listdir(path_data))
    first_file = True
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                if first_file:
                    st = obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                    first_file = False
                else:
                    st += obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
            except Exception:
                if verbose:
                    print("Can not read %s" % (file))
    return st


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

    # Save spectrogram plots in independent image files according to specify time length.
    print(f'Saving spectrograms every {spectrogram_interv/3600} hours ...')
    # Group streams of data per user defined time period
    startday = UTCDateTime(st[0].stats.starttime.date)
    endday = UTCDateTime(st[-1].stats.endtime.date)
    for c, i in tqdm(enumerate(range(int(startday.timestamp), int(endday.timestamp), spectrogram_interv))):
        st_cp = st.copy()
        st_cp = st_cp.slice(UTCDateTime(i), UTCDateTime(i) + spectrogram_interv)
        st_cp.sort(['starttime'])
        # Merge traces
        print(f'\nMerging data for the {i}th slot of {spectrogram_interv/3600} hour ...')
        st_cp.merge(method=0, fill_value=0)
        tr = st_cp[0]

        # Generate time and spectrograms plots
        fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(20, 10), dpi=100)
        t0 = tr.stats.starttime
        fig.suptitle(f'From {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")} until {tr.stats.endtime.strftime("%d-%b-%y at %H:%M:%S")} \n'
                     f'{tr.meta.location} \n Channel: {tr.meta.channel}')

        # Time intensity plot
        ax[0].plot(tr.times(reftime=t0), tr.data, 'k')
        ax[0].set_xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
        ax[0].set_ylabel('Intensity')

        # Spectrogram plot
        win_length = 1024
        hop_length = win_length // 16
        print(f'Computing spectrogram for the {c}th slot of {spectrogram_interv/3600} hour ...')
        D = librosa.stft(tr.data, hop_length=hop_length, n_fft=4096, win_length=None, window='hann', center=True)
        # Spectrogram magnitudes to a decibel scale
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max, amin=100, top_db=80)
        img = librosa.display.specshow(S_db, cmap='jet', sr=250, hop_length=hop_length, x_axis='time', y_axis='linear', ax=ax[1])
        #ax[1].set(title=f'Seconds relative to {t0}')
        ax[1].set_xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
        ax[1].xaxis.set_major_locator(MultipleLocator(20))
        ax[1].xaxis.set_minor_locator(MultipleLocator(5))
        fig.colorbar(img, ax=ax, format="%+2.f dB")

        # To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
        for ax_i in ax:
            ax_i.label_outer()

        os.makedirs(base_path_output + '/spectrograms_per_period', exist_ok=True)
        plt.savefig(f'{base_path_output}/spectrograms_per_period/{tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")}.png')
        plt.close()
