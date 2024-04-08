# Utilities

import obspy
from obspy.core import UTCDateTime
import os
from tqdm import tqdm
import numpy as np
from obspy.core.util.obspy_types import ObsPyException
from pathlib import Path
import bz2file as bz2
import pickle
import psutil


def read_data_from_folder(path_data, format, starttime, endtime, verbose=True):
    # Read all data files from directory
    dirlist = sorted(os.listdir(path_data))
    first_file = True
    st = []
    num_days_total = 0
    for file in tqdm(dirlist):
        file = os.path.join(path_data, file)
        if os.path.isfile(file):
            try:
                if first_file:
                    if format.lower() == 'bz2':
                        st = read_stream_bz2_pickle(file)
                    else:
                        st = obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                    first_file = False
                    # Memory report
                    startday = UTCDateTime(st[0].stats.starttime)
                    endday = UTCDateTime(st[0].stats.endtime)
                    num_days_total = num_days_total + (endday - startday)/86400
                    mem_usage = psutil.virtual_memory()
                    print(f'\nUsed RAM memory {mem_usage[2]}% (after loading {num_days_total: .2f} days of seismic data'
                          f' from {st[0].meta.location} and channel {st[0].meta.channel}).')
                    RAM_th = 95
                    if mem_usage[2] > RAM_th:
                        print(f'WARNING: RAM memory is full. The processing will be terribly slow!!!')
                else:
                    if format.lower() == 'bz2':
                        st += read_stream_bz2_pickle(file)
                    else:
                        st += obspy.read(file, format=format, headonly=False, starttime=starttime, endtime=endtime)
                    # Memory report
                    startday = UTCDateTime(st[0].stats.starttime)
                    endday = UTCDateTime(st[0].stats.endtime)
                    num_days_total = num_days_total + (endday - startday)/86400
                    mem_usage = psutil.virtual_memory()
                    print(f'\nUsed RAM memory {mem_usage[2]}% (after loading {num_days_total: .2f} days of seismic data'
                          f' from {st[0].meta.location} and channel {st[0].meta.channel}).')
                    RAM_th = 95
                    if mem_usage[2] > RAM_th:
                        print(f'WARNING: RAM memory is full. The processing will be terribly slow!!!')
            except Exception as e:
                if verbose:
                    print("Can not read %s (%s: %s)" % (file, type(e).__name__, e))
    return st


def detect_anomalies(stream, abs_th):
    # Detection of anomalous values
    for i, tr in enumerate(stream):
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
    for i, tr in enumerate(stream):
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

def write_stream_bz2_pickle(stream, filename):
    """
    Save stream into a bz2 file compressing pickle data.

    Arguments
    - stream: Obspy stream data
    - filename: The name of the file to write.
    """
    if not stream.traces:
        msg = 'Can not write empty stream to file.'
        raise ObsPyException(msg)

    # Check all traces for masked arrays and raise exception.
    for trace in stream.traces:
        if isinstance(trace.data, np.ma.masked_array):
            msg = 'Masked array writing is not supported. You can use ' + \
                  'np.array.filled() to convert the masked array to a ' + \
                  'normal array.'
            raise NotImplementedError(msg)

    '''
    # Add suffix if necessary
    format = Path(filename).suffix
    format = format[1:]
    if format is None:
        filename = filename + 'bz2'
    '''

    # Write compressed pickle file
    with bz2.BZ2File(filename, 'w') as fp:
        pickle.dump(stream, fp)


def read_stream_bz2_pickle(filename):
    """
    Read and return Stream from a bz2 file (with a compressed pickled) containing a ObsPy Stream object.

    Arguments
    - filename: Name of the pickled ObsPy Stream file to be read.

    Return: A ObsPy Stream object.
    """

    data = bz2.BZ2File(filename, 'rb')
    return pickle.load(data)
