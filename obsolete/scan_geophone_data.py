# Script that return the time span of a set of original files in SEG2 format from a directory.

import os
from tqdm import tqdm
import obspy


### Parameters ###
# Path to datafiles
path_data = './data/LaPalma/'


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
                    st = obspy.read(file, format=format, headonly=True)
                    first_file = False
                else:
                    st += obspy.read(file, format=format, headonly=True)
            except Exception:
                print("Can not read %s" % (file))
    return st


if __name__ == "__main__":
    # Read data
    st = read_data_from_directory(path_data, format='SEG2')

    # Short data temporally
    st.sort(['starttime'])

    # Print time span
    print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')
