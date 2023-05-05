# Utilities

import obspy
import os
from tqdm import tqdm


def read_data_from_folder(path_data, format, starttime, endtime, verbose=True):
    # Read all data files from directory
    dirlist = sorted(os.listdir(path_data))
    first_file = True
    st = []
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                if first_file:
                    st = obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                    first_file = False
                else:
                    st += obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
            except Exception as e:
                if verbose:
                    print("Can not read %s (%s: %s)" % (file, type(e).__name__, e))
    return st
