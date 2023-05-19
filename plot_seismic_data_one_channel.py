"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
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
from utils import read_data_from_folder
import numpy as np
import argparse
import yaml
import pickle
from scipy.ndimage import uniform_filter1d

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
        tr.data = obspy.signal.filter.bandstop(tr.data, 49, 51, tr.meta.sampling_rate, corners=8, zerophase=True)

    return tr

def prepare_fig(tr, prefix_name, a_min, a_max, fig, ax):
    print(f'Preparing figure...')

    # Decimation
    print(f'Decimation...')
    num_samples = len(tr.data)
    target_num_samples = 0.8 * fig.get_size_inches()[0] * fig.dpi  # Effective number of samples in the plot
    # More samples are considered than available in image resolution to allow zoom in vector format
    oversampling_factor = 100
    factor = int(num_samples / (target_num_samples * oversampling_factor))
    if factor > 1:
        tr.decimate(factor, no_filter=True)  # No antialiasing filtering because of lack of stability due to large decimation factor
    """ Two lengthy
    fm = num_samples * 0.5
    target_fm = target_num_samples * 0.5
    corner_freq = 0.4 * target_num_samples  # [Hz] Note that Nyquist is 0.5 * target_fm
    if corner_freq < fm / 2:  # To avoid ValueError
        tr.filter('lowpass', freq=corner_freq, corners=10, zerophase=True)    
    tr.interpolate(sampling_rate=target_fm, method='lanczos', a=20)
    """

    # Plotting and formatting
    plt.plot(tr.times(('matplotlib')), tr.data, 'k')
    ax.set(xlabel="Date",
           ylabel="Amplitude",
           title=f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel} '
                 f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} '
                 f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
           )
    #ax.set(xlim=["2005-06-01", "2005-08-31"])

    # Define the date format
    date_form_major = DateFormatter("%d-%b-%Y")
    ax.xaxis.set_major_formatter(date_form_major)
    date_form_minor = DateFormatter("%H")
    ax.xaxis.set_minor_formatter(date_form_minor)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0,24,4)))
    #fig.autofmt_xdate()  # Angle date

    # yaxis
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    # Change ticks
    ax.tick_params(axis='x', which='major', length=32, width=5, labelsize=18, rotation=0)
    ax.tick_params(axis='y', which='major', length=18, width=5)
    ax.tick_params(axis='both', which='minor', length=8, width=3, labelsize=10, rotation=0)

    # Change font size
    #ax.title.set_fontsize(18)
    #ax.xaxis.label.set_fontsize(18)
    #ax.yaxis.label.set_fontsize(18)
    #map(lambda p: p.set_fontsize(18), ax.get_xticklabels())
    #map(lambda p: p.set_fontsize(18), ax.get_yticklabels())

    # Use the parameters [a_min, a_max] if data values are inside that range. If not use the min and max data
    # values.
    min_val, max_val = np.percentile(tr.data, [0, 100])
    if a_min <= min_val and a_max >= max_val:
        ax.set(ylim=[a_min, a_max])

    ax.autoscale(enable=True, axis='x', tight=True)
    plt.tight_layout()
    return fig

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
        verbose = par['verbose']

        # Date preprocessing
        if starttime:
            starttime = UTCDateTime(starttime)
        if endtime:
            endtime = UTCDateTime(endtime)

        """
        Read, sort, merge, and filter data
        """
        tr = read_and_preprocessing(path_data, format_in, starttime, endtime)
        tr_rsam = tr.copy()

        """
        Plot seismic data
        """
        # Prepare figure
        plt.rcParams['font.size'] = 18 # Change font size
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(19, 10), dpi=100)
        fig = prepare_fig(tr, 'Plot', a_min, a_max, fig, ax)

        # Save figure
        save_figure(path_output, 'Plot', tr, fig, fig_format)

        plt.close(fig)
        del tr

        """
        Plot RSAM
        """
        # Computes RSAM
        n_samples = int(tr_rsam.meta.sampling_rate*60*10)  # Amount to 10 minutes
        tr_rsam.data = uniform_filter1d(abs(tr_rsam.data), size=n_samples)

        # Prepare figure
        plt.rcParams['font.size'] = 18 # Change font size
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(19, 10), dpi=100)
        fig = prepare_fig(tr_rsam, 'RSAM', 0, 1000, fig, ax)

        # Save figure
        save_figure(path_output, 'RSAM', tr_rsam, fig, fig_format)

        plt.close(fig)
        del tr_rsam


        """
        Day plot of seismic data
        """
        """
        file_name = f'{path_output}/day_plot_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
                    f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} ' \
                    f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}.png'
        # st.plot(type='dayplot', interval=interval_min, size=(4096, 2304))
        st.plot(type='dayplot', interval=time_interval_one_row, size=(4096, 2304), outfile=f'{file_name}')
        """
