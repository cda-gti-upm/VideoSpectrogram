"""
Plot seismic data: one plot for all given geophones and channels
Read datafiles of given specific locations (geophones) and channels and generate one figure with all the
plots.
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

def prepare_fig(tr, a_min, a_max, fig, ax):
    #plt.plot(tr.times(reftime=tr.stats.starttime), tr.data, 'k')
    ax.plot(tr.times(('matplotlib')), tr.data, 'k')
    ax.set(xlabel="Date",
           ylabel="Amplitude",
           title=f'Plot of {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel} '
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
    fig.autofmt_xdate()  # Angle date

    # yaxis
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    # Change ticks
    ax.tick_params(axis='both', which='major', length=12, width=4)
    ax.tick_params(axis='x', which='major', labelsize=28)
    ax.tick_params(axis='both', which='minor', length=8, width=3)
    ax.tick_params(axis='x', which='minor', labelsize=18, rotation=25)

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

    return fig, ax

def save_figure2(path_output, fig):
    plt.figure(fig)
    os.makedirs(path_output, exist_ok=True)
    file_name = f'{path_output}/plot_all_channels.png'
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
    plt.rcParams['font.size'] = 30  # Change font size
    fig, ax = plt.subplots(nrows=len(par_list), ncols=1, sharex=True, figsize=(41, 23), dpi=100)
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

        """
        Plot seismic data
        """
        # Prepare figure
        fig, ax[i] = prepare_fig(tr, a_min, a_max, fig, ax[i])

    # Save figure
    plt.tight_layout()
    save_figure2(path_output, fig)


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
