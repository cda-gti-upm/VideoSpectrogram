"""
Generate audio and video from infrasound seismic data
"""

from sonify_ext.sonify_input import sonify_input
from obspy import UTCDateTime
from tqdm import tqdm

"""
Arguments
"""
path_data = '../data/CSIC_LaPalma_Geophone8_Z'
starttime = "2021-11-29 00:30:00"
endtime = "2021-11-29 00:50:00"
speed_up_factor = 50


"""
Generate audio and video for given geophone and channel
"""
# Date preprocessing
if starttime:
    starttime = UTCDateTime(starttime)
if endtime:
    endtime = UTCDateTime(endtime)

# Audio and video generation
sonify_input(
    path_data=path_data,
    format_in='PICKLE',
    starttime=starttime,
    endtime=endtime,
    freqmin=None,
    freqmax=None,
    speed_up_factor=speed_up_factor,
    fps=10,  # Use fps=60 to ~recreate the JHEPC entry (slow to save!)
    output_dir='../results/audios',
    spec_win_dur=8,
    db_lim='smart',
)

