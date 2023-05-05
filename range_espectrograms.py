# Estimation of spectral power range and time amplitude range
# Description: estimate the range of spectral power and time amplitude values of data from a specific location
# (geophone) and channel # to plot series of spectrograms with the same absolute scale.


import os
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import obspy
from obspy.core import UTCDateTime
import librosa
import numpy as np
from utils import read_data_from_folder
import sys


# Parameters
# ----------------------------------------------------------------------------------------------------------------------
# Path to input datafiles regarding a specific location (geophone) and channel
path_data = './data/CSIC/LaPalma/Geophone_0/X/'  # './data/prueba'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". Alternative format using a ISO8601:2004 string:
                  # "2009-12-31T12:23:34.5"
endtime = None
verbose = True
# Spectrogram parameters (see function librosa.stft)
win_length = 1024
hop_length = win_length // 16
n_fft = 4096
window = 'hann'


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

    # Computing power spectral values to estimate their range.
    print(f'Estimation of power spectral range and time amplitude from data ...')
    global_min_S = sys.float_info.max
    global_max_S = 0
    global_min_a = sys.float_info.max
    global_max_a = sys.float_info.min
    for tr in tqdm(st):
        # Amplitude range in trace
        robust = False
        if robust:
            min_p, max_p = 2, 98
        else:
            min_p, max_p = 0, 100
        min_val, max_val = np.percentile(tr.data, [min_p, max_p])

        if min_val < global_min_a:
            global_min_a = min_val
        if max_val > global_max_a:
            global_max_a = max_val

        # Spectrogram computation
        D = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
        # Spectral power: spectrogram magnitudes to a decibel scale
        S_db = librosa.amplitude_to_db(np.abs(D), ref=1, amin=1e-5, top_db=None)

        # Spectrogram range in trace
        robust = False
        if robust:
            min_p, max_p = 2, 98
        else:
            min_p, max_p = 0, 100
        min_val, max_val = np.percentile(S_db, [min_p, max_p])

        if min_val < global_min_S:
            global_min_S = min_val
        if max_val > global_max_S:
            global_max_S = max_val

    print(f'Range of time amplitude values: ({global_min_a},{global_max_a}).')
    print(f'Range of power spectral values in dB: ({global_min_S},{global_max_S}).')



