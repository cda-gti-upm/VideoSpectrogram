# Script that reads datafiles of a specific location (geophone) and channel from a directory and save them in different
# files, every one storing the data of a given time interval.

import os
from tqdm import tqdm
import numpy as np
import obspy
from obspy.core import UTCDateTime
import scipy.signal
from utils import read_data_from_folder


### Parameters ###
# Path to input datafiles
path_data = './data/CSIC/LaPalma/Geophone_0/X/'
# Format of input datafiles
format_in='PICKLE'
# Path for output data
base_path_output = './data/LDF/CSIC/LaPalma/Geophone_0/X/'
# Format of output datafiles
format_out = 'PICKLE'
# Select time window
starttime = None  # Example: "2009-12-31 12:23:34". And using a ISO8601:2004 string: "2009-12-31T12:23:34.5"
endtime = None
time_interval = 24*60*60  # Length in seconds

verbose = True


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

    # Write data per time interval
    startday = UTCDateTime(st[0].stats.starttime.date)
    endday = UTCDateTime(st[-1].stats.endtime.date)
    os.makedirs(base_path_output, exist_ok=True)
    last_time = []
    for i in tqdm(range(int(startday.timestamp), int(endday.timestamp), time_interval)):
        st_day = st.copy()
        st_day = st_day.slice(UTCDateTime(i), UTCDateTime(i) + time_interval)
        st_day.sort(['starttime'])
        # Merge traces
        st_day.merge(method=0, fill_value=0)
        # Write data to a file
        st_day.write(f'{base_path_output}/{st_day[0].meta.network}_{st_day[0].meta.station}_{st_day[0].meta.location}_{st_day[0].meta.channel}_{UTCDateTime(i).strftime("%d-%b-%Y at %H.%M.%S")}.{format_out.lower()}', format=format_out)
        last_time = i+time_interval

    # Write last incomplete time interval
    if (last_time+1) < int(endday.timestamp):
        st_day = st.copy()
        st_day = st_day.slice(UTCDateTime(last_time+1), endday.timestamp)
        st_day.sort(['starttime'])
        # Merge traces
        st_day.merge(method=0, fill_value=0)
        # Write data to a file
        st_day.write(f'{base_path_output}/{st_day[0].meta.network}_{st_day[0].meta.station}_{st_day[0].meta.location}_{st_day[0].meta.channel}_{UTCDateTime(last_time+1).strftime("%d-%b-%Y at %H.%M.%S")}.{format_out.lower()}', format=format_out)