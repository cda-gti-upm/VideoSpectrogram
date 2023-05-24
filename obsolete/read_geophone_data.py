# Script to read all the original files in SEG2 format from a directory and save the data as a pickle file that contains
# one stream and multiple traces.

import os
from tqdm import tqdm
import obspy


# Path to datafiles
path_data = './data/LaPalma/'
# Path for output data (pickle format)
path_output = 'CSIC_LaPalma_OneStream_MultipleTraces.pickle'
verbose = True


def read_data_from_directory(path_data, format):
    # Read all data files from directory
    dirlist = sorted(os.listdir(path_data))
    first_file = True
    print('READING DATA FILES')
    print('=============================')
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                if first_file:
                    st = obspy.read(file, format=format, headonly=False)
                    first_file = False
                else:
                    st += obspy.read(file, format=format, headonly=False)
            except Exception:
                if verbose:
                    print("Can not read %s" % (file))
    return st


def detect_anomalies(stream, abs_th):
    # Detection of anomalous large data values
    print('DETECTION OF ANOMALOUS VALUES')
    print('=============================')
    for i, tr in enumerate(tqdm(stream)):
        ind = abs(tr.data) > abs_th
        if any(ind):
            print(f'Trace {i}, values: {tr.data[ind]}')
        #st[0].data[ind] = val

def write_datafiles_location_channel(stream):
    # Add network, station, location, channel, and id information.
    channels = ['X', 'Y', 'Z']
    for i, trace in enumerate(stream):
        network = 'CSIC'
        station = 'LaPalma'
        location = f'Geophone_{i // 3}'
        channel = channels[i % 3]
        trace.meta.network = network
        trace.stats.network = network
        trace.meta.station = station
        trace.stats.station = station
        trace.meta.location = location
        trace.stats.location = location
        trace.meta.channel = channel
        trace.stats.channel = channel
        trace.id = f'{network}.{station}.{location}.{channel}'

        # Save data into pickle format
        file_name = os.path.splitext(os.path.basename(file))[0]
        dir_name = f'./data/{network}/{station}/{location}/{channel}'
        os.makedirs(dir_name, exist_ok=True)
        trace.write(f'{dir_name}/{file_name}.pickle', format='PICKLE')

# Read data
st = read_data_from_directory(path_data, format='SEG2')

# Detect anomalous data
detect_anomalies(st, abs_th=1000000)

# Short data temporally
st.sort(['starttime'])
print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

# Detect anomalous data
detect_anomalies(st, abs_th=1000000)

# Save data into pickle format
print('SAVING DATA FILES')
print('=============================')
write_datafiles_location_channel
st.write(path_output, format='PICKLE')