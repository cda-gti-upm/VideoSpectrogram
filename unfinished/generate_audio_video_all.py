"""
Generate audio and video from infrasound seismic data
"""

from sonify_ext.sonify_input import sonify_input
from obspy import UTCDateTime
from tqdm import tqdm

"""
Arguments
"""
path_data = ['../data/CSIC_LaPalma_Geophone 0_X',
             '../data/CSIC_LaPalma_Geophone 0_Y',
             '../data/CSIC_LaPalma_Geophone 0_Z',
             '../data/CSIC_LaPalma_Geophone 1_X',
             '../data/CSIC_LaPalma_Geophone 1_Y',
             '../data/CSIC_LaPalma_Geophone 1_Z',
             '../data/CSIC_LaPalma_Geophone 2_X',
             '../data/CSIC_LaPalma_Geophone 2_Y',
             '../data/CSIC_LaPalma_Geophone 2_Z',
             '../data/CSIC_LaPalma_Geophone 3_X',
             '../data/CSIC_LaPalma_Geophone 3_Y',
             '../data/CSIC_LaPalma_Geophone 3_Z',
             '../data/CSIC_LaPalma_Geophone 4_X',
             '../data/CSIC_LaPalma_Geophone 4_Y',
             '../data/CSIC_LaPalma_Geophone 4_Z',
             '../data/CSIC_LaPalma_Geophone 5_X',
             '../data/CSIC_LaPalma_Geophone 5_Y',
             '../data/CSIC_LaPalma_Geophone 5_Z',
             '../data/CSIC_LaPalma_Geophone 6_X',
             '../data/CSIC_LaPalma_Geophone 6_Y',
             '../data/CSIC_LaPalma_Geophone 6_Z',
             '../data/CSIC_LaPalma_Geophone 7_X',
             '../data/CSIC_LaPalma_Geophone 7_Y',
             '../data/CSIC_LaPalma_Geophone 7_Z',
             ]


starttime = "2021-11-23 00:00:01"
endtime = "2021-12-01 00:00:07"
interval = 6 * 60 * 60  # In seconds


"""
Generate audio and video for every geophone and channel
"""
# Process every source of data: geophone and channel
for path_i in path_data:
    # Date preprocessing
    if starttime:
        starttime = UTCDateTime(starttime)
    if endtime:
        endtime = UTCDateTime(endtime)

    # Process every time interval
    for i in tqdm(range(int(starttime.timestamp), int(endtime.timestamp) + 1, interval)):
        sonify_input(
            path_data=path_i,
            format_in='PICKLE',
            starttime=UTCDateTime(i),
            endtime=UTCDateTime(i+interval-1),
            freqmin=20/200,
            freqmax=20000/200,
            speed_up_factor=200,
            fps=10,  # Use fps=60 to ~recreate the JHEPC entry (slow to save!)
            output_dir='../results/audios',
            spec_win_dur=8,
            db_lim='smart',
        )

