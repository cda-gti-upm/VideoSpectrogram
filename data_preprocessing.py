"""
Data preprocessing of original data files

Every data file contains 24 traces corresponding to:
- 8 geophones
- 3 channels (x, y, and z) per geophone

The assumed order of the traces are:
- Geophone 0, channel X
- Geophone 0, channel Y
- Geophone 0, channel Z
- Geophone 1, channel X
- ...
- Geophone 7, channel Z

Processing steps:
- Read source data files
- Split data by geophone and channel
- Correct geophones response
- Demean trend data
- Save data in large datafile to improve posterior analysis
"""


import os
from tqdm import tqdm
import obspy
from obspy.core import UTCDateTime
import scipy.signal
import argparse
import yaml
import shutil
from utils import read_data_from_folder


"""
Functions
"""
def split_data_per_location_channel(stream, network, station):
    # Split the info of every datafile (8 locations/geophones X 3 channels) into multiple (24) traces according to the
    # network, station, location, and channel information.
    channels = ['X', 'Y', 'Z']
    n_c = len(channels)
    trace_list = []
    for i, trace in enumerate(stream):
        location = f'Geophone {i // n_c}'
        channel = channels[i % n_c]
        trace.meta.network = network
        trace.stats.network = network
        trace.meta.station = station
        trace.stats.station = station
        trace.meta.location = location
        trace.stats.location = location
        trace.meta.channel = channel
        trace.stats.channel = channel
        trace.id = f'{network}.{station}.{location}.{channel}'
        trace_list.append(trace)

    return trace_list

def write_data_per_location_channel(trace_list, filename, path_output, format_out):
    # Write data into a new hierarchy of folders and files according to the network, station, location, and channel information.
    # Save data into pickle format
    for i, trace in enumerate(trace_list):
        file_name = os.path.splitext(os.path.basename(file))[0]
        dir_name = f'{path_output}/{trace.meta.network}/{trace.meta.station}/{trace.meta.location}/{trace.meta.channel}'
        os.makedirs(dir_name, exist_ok=True)
        trace.write(f'{dir_name}/{file_name}.pickle', format=format_out)

def fast_scandir(dirname):
    subfolders = [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders


if __name__ == "__main__":
    """
    # Process input arguments given by the configuration file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("conf_path")
    args = parser.parse_args()
    with open(args.conf_path, mode="rb") as file:
        par = yaml.safe_load(file)

    # Simplify variable names
    path_data = par['paths']['path_data']
    path_output = par['paths']['path_output']
    format_in = par['data_format']['format_in']
    format_out = par['data_format']['format_out']
    correc_f = par['sensor_correction']['correc_f']
    demean_f = par['filter']['demean_f']
    a = par['sensor_correction']['a']
    b = par['sensor_correction']['b']
    network = par['data_info']['network']
    station = par['data_info']['station']
    time_interval = par['time_interval']
    verbose = par['verbose']


    """
    Step 1: load data files and apply sensor correction
    
    Read all data files from directory and creates a temporal hierarchy of folders and files according to the network,
    station, location, and channel information
    """
    print(f'Step 1 out 3: loading and correcting data ...')
    dirlist = sorted(os.listdir(path_data))
    path_output_tmp = path_output+'/tmp'
    print(f'Create temporal data in {path_output_tmp}')
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                # Read data file
                st = obspy.read(file, format=format_in, headonly=False)
            except Exception as e:
                if verbose:
                    print("Can not read %s (%s: %s)" % (file, type(e).__name__, e))

            # Correct sensor response
            if correc_f:
                z, p, k = scipy.signal.tf2zpk(b, a)
                paz = {
                    'poles': p,
                    'zeros': z,
                    'gain': k,
                    'sensitivity': 1}
                st.simulate(paz_remove=paz)

            # Demean
            if demean_f:
                st.detrend('demean')

            trace_list = split_data_per_location_channel(st, network=network, station=station)
            write_data_per_location_channel(trace_list, file, path_output_tmp, format_out)


    """ 
    Step 2: store data in large size files to speed up posterior data processing
    
    Reads datafiles per location (geophone) and channel from the previously created hierarchy of files and save them
    in large size # files to speed up posterior data processing. The size of every file is determined by the specified
    time interval.
    """
    print(f'Step 2 out 3: store data in large data files ...')
    # Read data
    path_list = fast_scandir(f'{path_output_tmp}')
    for path_i in tqdm(path_list):
        print(f'Reading data from {path_i}')
        st = read_data_from_folder(path_i, format_out, starttime=None, endtime=None)

        # Skip if no data in directory
        if not st:
            print(f'No data files in {path_i}')
            continue

        # Sort data
        st.sort(['starttime'])
        print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

        # Write data per time interval
        startday = UTCDateTime(st[0].stats.starttime.date)
        endday = UTCDateTime(st[-1].stats.endtime.date)
        last_time = []
        for i in tqdm(range(int(startday.timestamp), int(endday.timestamp) + 1, time_interval)):
            st_day = st.slice(UTCDateTime(i), UTCDateTime(i) + time_interval - 1)
            st_day.sort(['starttime'])
            # Merge traces
            st_day.merge(method=0, fill_value=0)
            # Write data to a file
            path_file = f'{path_output}/{st_day[0].meta.network}_{st_day[0].meta.station}_{st_day[0].meta.location}_' \
                        f'{st_day[0].meta.channel}/'
            os.makedirs(path_file, exist_ok=True)
            file_name = f'{path_file}{UTCDateTime(i).strftime("%d-%b-%Y at %H.%M.%S")}' \
                        f'.{format_out.lower()}'
            print(f'Writing file: {file_name} with data from {UTCDateTime(i).strftime("%d-%b-%Y at %H.%M.%S")} '
                  f'until {UTCDateTime(i + time_interval-1).strftime("%d-%b-%Y at %H.%M.%S")}')
            st_day.write(file_name, format=format_out)
            last_time = i + time_interval - 1


    """
    Step 3: delete temporal information
    """
    print(f'Step 3 out 3: delete temporal data data ...')
    shutil.rmtree(f'{path_output_tmp}')

