# Utilities

import obspy
import os
from tqdm import tqdm
import numpy as np


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


def detect_anomalies(stream, abs_th):
    # Detection of anomalous values
    for i, tr in enumerate(tqdm(stream)):
        # Detection of not-a-number values
        indnan = np.isnan(tr.data)
        if any(indnan):
            print(f'List of indexes containing a not-a-number value (NaN) in Trace {i}:')
            print(f'Indexes: {np.where(indnan)}')
        """
        else:
            print(f'Trace {i} does not contain not-a-number values (NaN)')
        """

        # Detection of infinite values
        indinf = np.isinf(tr.data)
        if any(indinf):
            print(f'List of indexes containing a infinite value (inf) in Trace {i}:')
            print(f'Indexes: {np.where(indinf)}')
        """
        else:
            print(f'Trace {i} does not contain infinite values (inf)')
        """

        # Detection of very large values
        indlarge = abs(tr.data) > abs_th
        if any(indlarge):
            print(f'Indexes: {np.where(indlarge)}')
            print(f'Values: {tr.data[indlarge]}')
        """
        else:
            print(f'Trace {i} does not contain large values')
        """
        #st[0].data[ind] = val


def correct_data_anomalies(stream, abs_th):
    # Correction of anomalous values
    for i, tr in enumerate(tqdm(stream)):
        # Correction of not-a-number values
        indnan = np.isnan(tr.data)
        tr.data[indnan] = 0

        # Correction of infinite values
        indinf = np.isinf(tr.data)
        tr.data[indinf] = 0

         # Correction of very large values
        indlarge = abs(tr.data) > abs_th
        tr.data[indlarge] = 0

    return stream