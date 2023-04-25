# Script that reads datafiles of a specific location (geophone) and channel from a directory and computes a spectogram
# per data file using obspy functions. Spectrogram plots are saved in independent image files.


import os
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import obspy
from obspy.core import UTCDateTime


# Parameters -----------------------------------------------------------------------------------------------------------
# Path to input datafiles regarding a specific location (geophone) and channel
path_data = './data/CSIC/LaPalma/Geophone_0/X/'
# Path for output plots
base_path_output = './data/spectrograms'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". Alternative format using a ISO8601:2004 string:
                  # "2009-12-31T12:23:34.5"
endtime = None
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
    st = read_data_from_folder(path_data, format_in, starttime, endtime)

    # Sort data
    print(f'Sorting data ...')
    st.sort(['starttime'])
    print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

    # Save spectrograms in independent image files
    print(f'Saving spectrograms for every data file ...')
    print(f'Sample numer per data file: {len(st[0].data)}')
    for tr in tqdm(st):
        fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(10, 8), dpi=100)
        t0 = tr.stats.starttime
        fig.suptitle(f'From {t0} to {tr.stats.endtime}')

        ax[0].plot(tr.times(reftime=t0), tr.data, 'k')
        ax[0].set_xlabel(f'Seconds relative to {t0}')
        ax[0].set_ylabel('Intensity')

        tr.spectrogram(log=False, wlen=1000 / tr.meta.sampling_rate, dbscale=True,
                         cmap='jet', axes=ax[1], show=False, mult=16)
        ax[1].set_xlabel(f'Seconds relative to {t0}')
        ax[1].set_ylabel('Frequency [Hz]')

        # To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
        for ax_i in ax:
            ax_i.label_outer()

        os.makedirs(base_path_output + '/all_spect', exist_ok=True)
        plt.savefig(f'{base_path_output}/all_spect/{t0.strftime("d%dm%my%y__H%H-M%MS%S")}.png')
        plt.close()
