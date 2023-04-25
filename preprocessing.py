# Script to read all the original files in SEG2 format from a directory and creates a new hierarchy of folders and files
# according to the network, station, location, channel, and information. Optionally, the sensor response is corrected.

import os
from tqdm import tqdm
import obspy
import scipy.signal


# Parameters -----------------------------------------------------------------------------------------------------------
# Path to input datafiles
path_data = './data/LaPalma/'
# Path for output data
base_path_output = './data'
# Sensor correction flag
correc_f = True
# Sensor correction parameters: coefficients of the numerator and denominator of the transfer function
b = [1.0000, -1.5365, 0.6507]   # Numerator
a = [-1.0000, 1.9388, -0.9388]  # Denominator
verbose = True


# Internal parameters
# Format of input datafiles
format_in = 'SEG2'
# Format of output datafiles
format_out = 'PICKLE'


# Functions
def split_data_per_location_channel(stream):
    # Split the info of every datafile (8 locations/geophones X 3 channels) into multiple (24) traces according to the
    # network, station, location, and channel information.
    channels = ['X', 'Y', 'Z']
    network = 'CSIC'
    station = 'LaPalma'
    n_c = len(channels)
    trace_list = []
    for i, trace in enumerate(stream):
        location = f'Geophone_{i // n_c}'
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

def write_data_per_location_channel(trace_list):
    # Write data into a new hierarchy of folders and files according to the network, station, location, and channel information.
    # Save data into pickle format
    for i, trace in enumerate(trace_list):
        file_name = os.path.splitext(os.path.basename(file))[0]
        dir_name = f'{base_path_output}/{trace.meta.network}/{trace.meta.station}/{trace.meta.location}/{trace.meta.channel}'
        os.makedirs(dir_name, exist_ok=True)
        trace.write(f'{dir_name}/{file_name}.pickle', format=format_out)

def detect_anomalies(stream, file, abs_th):
    # Detection of anomalous large data values
    for i, tr in enumerate(stream):
        ind = abs(tr.data) > abs_th
        if any(ind):
            print(f'Anomaly in file {file}, trace {i}, values: {tr.data[ind]}')


# Main program
if __name__ == "__main__":
    # Read all data files from directory
    dirlist = sorted(os.listdir(path_data))
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                st = obspy.read(file, format=format_in, headonly=False)
                if correc_f:
                    #st_orig = st.copy()
                    z, p, k = scipy.signal.tf2zpk(b, a)
                    paz = {
                        'poles': p,
                        'zeros': z,
                        'gain': k,
                        'sensitivity': 1}
                    st.simulate(paz_remove=paz)
                    #st_orig[0].plot()
                    #st[0].plot()

                # Detect anomalous data
                detect_anomalies(st, file, abs_th=1000000)
                trace_list = split_data_per_location_channel(st)
                write_data_per_location_channel(trace_list)
            except Exception:
                if verbose:
                    print("Can not read %s" % (file))
