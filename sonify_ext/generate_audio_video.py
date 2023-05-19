"""
Generate audio and video from infrasound seismic data
"""

from sonify_ext.sonify_input import sonify_input
from obspy import UTCDateTime
from tqdm import tqdm

"""
Arguments
"""
path_data = '../data/CSIC_LaPalma_Geophone 0_X'


starttime = "2021-11-29 00:00:00"
endtime = "2021-11-30 00:03:00"


"""
Generate audio and video for given geophone and channel
"""
# Date preprocessing
if starttime:
    starttime = UTCDateTime(starttime)
if endtime:
    endtime = UTCDateTime(endtime)

sonify_input(
    path_data=path_data,
    format_in='PICKLE',
    starttime=starttime,
    endtime=endtime,
    freqmin=20/200,
    freqmax=20000/200,
    speed_up_factor=200,
    fps=10,  # Use fps=60 to ~recreate the JHEPC entry (slow to save!)
    output_dir='../results/audios',
    spec_win_dur=8,
    db_lim='smart',
)

