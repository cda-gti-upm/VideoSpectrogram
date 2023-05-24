# Script that reads datafiles of a specific location (geophone) and channel from a directory and save them in different
# files, every one storing the data of a whole day.

import os
from tqdm import tqdm
import numpy as np
import obspy
from obspy.core import UTCDateTime
import scipy.signal


### Parameters ###
# Path to input datafiles
path_data = './data/CSIC/LaPalma/Geophone_0/X/'
# Format of input datafiles
format_in='PICKLE'
# Path for output data
base_path_output = './data/corrected'
# Format of output datafiles
format_out = 'PICKLE'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". And using a ISO8601:2004 string: "2009-12-31T12:23:34.5"
endtime = None
# Sensor correction flag
correc_f = False
# Sensor correction parameters: numerator and denominator coefficients of the transfer function
b = [1.0000, -1.5365, 0.6507]  # Numerator
a = [-1.0000, 1.9388, -0.9388] # Denominator
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
                    first_file = False
                else:
                    st += obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
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

    # Write data per day
    startday = UTCDateTime(st[0].stats.starttime.date)
    endday = UTCDateTime(st[-1].stats.endtime.date)
    delta_day = 24*60*60  # Day length in seconds
    os.makedirs(base_path_output, exist_ok=True)
    for i in tqdm(range(int(startday.timestamp), int(endday.timestamp), delta_day)):
        st_day = st.copy()
        st_day = st_day.slice(UTCDateTime(i), UTCDateTime(i) + delta_day)
        st_day.sort(['starttime'])
        # Merge traces
        st_day.merge(method=0, fill_value=0)
        if correc_f:
            #st_day_orig = st_day.copy()
            z, p, k = scipy.signal.tf2zpk(b, a)
            paz = {
                'poles': p,
                'zeros': z,
                'gain': k,
                'sensitivity': 1}
            st_day.simulate(paz_remove=paz)
            #st_day_orig[0].plot()
            #st_day[0].plot()

        # Detect anomalous data
        detect_anomalies(st_day, abs_th=1000000)
        #if np.ma.isMaskedArray(st_day[0].data):
        #    st_day[0].data = st_day[0].data.filled()
        st_day.write(f'{base_path_output}/{st_day[0].meta.network}_{st_day[0].meta.station}_{st_day[0].meta.location}_{st_day[0].meta.channel}_{UTCDateTime(i).strftime("d%dm%my%y__H%H-M%MS%S")}.{format_out.lower()}', format=format_out)