# Script that reads datafiles per day of a specific location (geophone) and channel from a directory and makes time
# series plots.

import os
from tqdm import tqdm
import matplotlib.pyplot as plt
import obspy
from obspy.core import UTCDateTime


### Parameters ###
# Path to input datafiles
path_data = './data/CSIC_LaPalma_Geophone_0_X/'
# Format of input datafiles
format_in='PICKLE'
'''
# Path for output data
base_path_output = './data'
# Format of output datafiles
format_out = 'PICKLE'
'''
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". And using a ISO8601:2004 string: "2009-12-31T12:23:34.5"
endtime = None
verbose = True


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
                    print(f'Read file: {file}')
                    first_file = False
                else:
                    st += obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                    print(f'Read file: {file}')
            except Exception:
                if verbose:
                    print("Can not read %s" % (file))
    return st

def detect_anomalies(stream, abs_th):
    # Detection of anomalous large data values
    for i, tr in enumerate(tqdm(stream)):
        ind = abs(tr.data) > abs_th
        if any(ind):
            print(f'Trace {i}, values: {tr.data[ind]}')
        #st[0].data[ind] = val


if __name__ == "__main__":
    # Date preprocessing
    if starttime:
        starttime = UTCDateTime(starttime)
    if endtime:
        endtime = UTCDateTime(endtime)

    # Read data
    st = read_data_from_folder(path_data, format_in, starttime, endtime)

    # Sort data
    st.sort(['starttime'])
    print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

    # TODO: ver opciones para representar series temporales con matplotlib y la incluida en Stream
    # Plot time series from all data using matplotlib
    # Use common reference time and have x-Axis as relative time in seconds.
    t0 = st[0].stats.starttime
    plt.figure(figsize=(64, 24), dpi=80)
    plt.plot(st[0].times(reftime=t0), st[0].data, 'r')
    plt.xlabel(f'Seconds relative to {t0}')
    plt.savefig('Full_TimeSeries_One_Row.png')
    plt.show()

    # Day plot
    st.plot(type='dayplot', interval=180, size=(800 * 8, 600 * 8))
    st.plot(type='dayplot', interval=180, size=(800 * 8, 600 * 8), outfile='Full_TimeSeries_Multiple_Rows.png')

    # TODO: Interactive plot
    '''
    # Interactive plot
    fig = px.line(x=st[0].times(reftime=t0), y=st[0].data)
    fig.show()
    '''



    # TODO: Another option would be to plot absolute times by using ...
    # Trace.times(type='matplotlib') and letting matplotlib know that x-Axis has
    # absolute times, by using ax.xaxis_date() and fig.autofmt_xdate()

    '''
    for (tr, ax) in zip(st2, axes2):
        ax.plot(tr.times(type='matplotlib'), tr.data)
        ax.xaxis_date()
        fig2.autofmt_xdate()

    # Merge the data together and plot in a similar way in the bottom Axes
    st2.merge(method=1)
    axes[-1].plot(st2[0].times(type='matplotlib'), st2[0].data, 'r')
    axes[-1].set_xlabel(f'Absolute time')
    ax.xaxis_date()
    fig2.autofmt_xdate()
    plt.show()
    '''