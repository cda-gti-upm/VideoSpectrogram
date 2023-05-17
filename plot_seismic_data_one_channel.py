"""
Plot seismic data
# Description: read datafiles of a specific location (geophone) and channel and plot seismic data (standard plot and a day plot).
# If f_plot_datafiles = True, a time plot figure is saved per acquisition file.
"""

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
import argparse
import yaml

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

    """ Process every set of parameters """
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

        """
        Plot seismic data
        """
        fig = plt.figure(figsize=(41, 23), dpi=100)
        ax = fig.add_subplot(111)
        plt.plot(st[0].times(reftime=tr.stats.starttime), tr.data, 'k')
        plt.xlabel(f'Time relative to {tr.stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
        ax.xaxis.set_major_formatter(librosa.display.TimeFormatter(unit=None, lag=False))
        ax.xaxis.set_major_locator(MaxNLocator(prune=None, steps=[1, 1.5, 5, 6, 10]))
        plt.ylabel('Intensity')
        # Use the parameters [a_min, a_max] if data values are inside that range. If not use the min and max data
        # values.
        min_val, max_val = np.percentile(tr.data, [0, 100])
        if a_min <= min_val and a_max >= max_val:
            plt.ylim([a_min, a_max])

        os.makedirs(path_output, exist_ok=True)
        file_name = f'{path_output}/plot_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
                    f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} ' \
                    f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}.png'
        plt.savefig(f'{file_name}')

        """
        Day plot of seismic data
        """
        file_name = f'{path_output}/day_plot_{tr.meta.network}_{tr.meta.station}_{tr.meta.location}_{tr.meta.channel}_' \
                    f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} ' \
                    f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}.png'
        # st.plot(type='dayplot', interval=interval_min, size=(4096, 2304))
        st.plot(type='dayplot', interval=time_interval_one_row, size=(4096, 2304), outfile=f'{file_name}')
