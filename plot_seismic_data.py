# Plot seismic data
# Read datafiles of a specific location (geophone) and channel, select a time window and plot seismic
# data (standard plot and a day plot).
# If f_plot_datafiles = True, a time plot figure is saved per acquisition file.


import os
from tqdm import tqdm
import obspy
from obspy.core import UTCDateTime
import matplotlib.pyplot as plt


# Parameters -----------------------------------------------------------------------------------------------------------
# Path to input datafiles regarding a specific location (geophone) and channel
path_data = './data/CSIC/LaPalma/Geophone_0/X/'
# Path for output plots
base_path_output = './data/plots'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". Alternative format using a ISO8601:2004 string:
                  # "2009-12-31T12:23:34.5"
endtime = None
# Flag to save plots from data files independently
f_plot_datafiles = False
verbose = True


# Internal parameters
# Format of input datafiles
format_in = 'PICKLE'


# Functions
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
            t0 = tr.stats.starttime
            plt.figure(figsize=(10, 4), dpi=100)
            plt.plot(tr.times(reftime=t0), tr.data, 'k')
            plt.xlabel(f'Seconds relative to {t0}')
            os.makedirs(base_path_output + '/all_plots', exist_ok=True)
            plt.savefig(f'{base_path_output}/all_plots/{t0.strftime("d%dm%my%y__H%H-M%MS%S")}.png')
            plt.close()

    # Merge traces
    print(f'Merging data ...')
    st.merge(method=0, fill_value=0)

    # Plot seismic data
    # Matplotlib interface
    # Use common reference time and have x-Axis as relative time in seconds.
    t0 = st[0].stats.starttime
    plt.figure(figsize=(19,10), dpi=100)
    plt.plot(st[0].times(reftime=t0), st[0].data, 'k')
    plt.xlabel(f'Seconds relative to {t0}')
    os.makedirs(base_path_output, exist_ok=True)
    plt.savefig(f'{base_path_output}/Full_Seismic_data.png')
    plt.show()

    # Day plot of seismic data
    interval_min = 12*60
    st.plot(type='dayplot', interval=interval_min, size=(1900, 1000))
    st.plot(type='dayplot', interval=interval_min, size=(1900, 1000), outfile=f'{base_path_output}/Full_TimeSeries_Multiple_Rows.png')