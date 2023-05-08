# Plot seismic data
# Description: read datafiles of a specific location (geophone) and channel and plot seismic data (standard plot and a day plot).
# If f_plot_datafiles = True, a time plot figure is saved per acquisition file.


import os

import librosa.display
from tqdm import tqdm
import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator, AutoLocator, MaxNLocator)
from utils import read_data_from_folder
import numpy as np


# Parameters -----------------------------------------------------------------------------------------------------------
# Path to input datafiles regarding a specific location (geophone) and channel
path_data = './data/LDF/CSIC/LaPalma/Geophone_0/X/'
# Path for output plots
base_path_output = './data/plots'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". Alternative format using a ISO8601:2004 string:
                  # "2009-12-31T12:23:34.5"
endtime = None
# Flag to save plots from data files independently
f_plot_datafiles = True
verbose = True
# Maximum and minimum amplitude to represent time plots. Use 'range_espectrograms.py' to infer such as values.
a_max = 40000  # 433438
a_min = -40000  # -289208
# Flag to filter 50 Hz
filter_50Hz = True
sr = 250


# Internal parameters
# Format of input datafiles
format_in = 'PICKLE'


# Main program
if __name__ == "__main__":
    # Date preprocessing
    if starttime:
        starttime = UTCDateTime(starttime)
    if endtime:
        endtime = UTCDateTime(endtime)

    # Read data
    print(f'Reading data ...')
    st = read_data_from_folder(path_data, format_in, starttime, endtime)

    # Sort data
    print(f'Sorting data ...')
    st.sort(['starttime'])
    print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

    # Save seismic plots in independent image files
    if f_plot_datafiles:
        print(f'Saving plots for every data file ...')
        for tr in tqdm(st):
            # Filtering 50 Hz
            if filter_50Hz:
                tr.data = obspy.signal.filter.bandstop(tr.data, 49, 51, sr, corners=8, zerophase=True)
            fig = plt.figure(figsize=(10, 4), dpi=100)
            ax = fig.add_subplot(111)
            plt.plot(tr.times(reftime=tr.stats.starttime), tr.data, 'k')
            plt.xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
            ax.xaxis.set_major_formatter(librosa.display.TimeFormatter(unit=None, lag=False))
            ax.xaxis.set_major_locator(MaxNLocator(prune=None, steps=[1, 1.5, 5, 6, 10]))
            plt.ylabel('Intensity')
            # Use the parameters [a_min, a_max] if data values are inside that range, if not use the min and max data values.
            min_val, max_val = np.percentile(tr.data, [0, 100])
            if a_min <= min_val and a_max >= max_val:
                plt.ylim([a_min, a_max])
            os.makedirs(base_path_output + '/all_plots', exist_ok=True)
            plt.savefig(f'{base_path_output}/all_plots/{tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")}.png')
            plt.close()

    # Merge traces
    print(f'Merging data ...')
    st.merge(method=0, fill_value=0)
    tr = st[0]

    # Filtering 50 Hz
    if filter_50Hz:
        print(f'Filtering 50 Hz signal ...')
        tr.data = obspy.signal.filter.bandstop(tr.data, 49, 51, sr, corners=8, zerophase=True)

    # Plot seismic data
    fig = plt.figure(figsize=(19,10), dpi=100)
    ax = fig.add_subplot(111)
    plt.plot(st[0].times(reftime=tr.stats.starttime), st[0].data, 'k')
    plt.xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
    ax.xaxis.set_major_formatter(librosa.display.TimeFormatter(unit=None, lag=False))
    ax.xaxis.set_major_locator(MaxNLocator(prune=None, steps=[1, 1.5, 5, 6, 10]))
    plt.ylabel('Intensity')
    # Use the parameters [a_min, a_max] if data values are inside that range, if not use the min and max data values.
    min_val, max_val = np.percentile(tr.data, [0, 100])
    if a_min <= min_val and a_max >= max_val:
        plt.ylim([a_min, a_max])
    os.makedirs(base_path_output, exist_ok=True)
    plt.savefig(f'{base_path_output}/Full_Seismic_data_1_channel.png')

    # Day plot of seismic data
    interval_min = 24*60
    #st.plot(type='dayplot', interval=interval_min, size=(1900, 1000))
    st.plot(type='dayplot', interval=interval_min, size=(1900, 1000), outfile=f'{base_path_output}/Full_TimeSeries_Multiple_Rows_1_Channel.png')