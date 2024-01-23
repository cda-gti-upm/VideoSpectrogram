import obspy
from utils import read_data_from_folder
import obspy.signal.filter
import webbrowser


def read_and_preprocessing(path, in_format, start, end, filter_50Hz_f):
    # Read data
    print(f'Reading data ...')
    stream = read_data_from_folder(path, in_format, start, end)

    # Sort data
    print(f'Sorting data ...')
    stream.sort(['starttime'])
    print(f'Data spans from {stream[0].stats.starttime} until {stream[-1].stats.endtime}')

    # Merge traces
    print(f'Merging data ...')
    stream.merge(method=0, fill_value=0)
    trace = stream[0]

    # Filtering 50 Hz
    if filter_50Hz_f:
        print(f'Filtering 50 Hz signal ...')
        trace.data = obspy.signal.filter.bandstop(trace.data, 49, 51, trace.meta.sampling_rate, corners=8,
                                                  zerophase=True)

    return trace


def open_browser(port):
    webbrowser.open_new("http://localhost:{}".format(port))


def generate_title(tr, prefix_name):
    title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel}, from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
    return title


