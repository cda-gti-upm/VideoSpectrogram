from sonify.sonify import sonify
from sonify.sonify import sonify_input
from obspy import UTCDateTime

"""
sonify(
    network='AV',
    station='ILSW',
    channel='BHZ',
    starttime=UTCDateTime(2019, 6, 20, 23, 10),
    endtime=UTCDateTime(2019, 6, 21, 0, 30),
    freqmin=1,
    freqmax=23,
    speed_up_factor=200,
    fps=1,  # Use fps=60 to ~recreate the JHEPC entry (slow to save!)
    spec_win_dur=8,
    db_lim=(-180, -130),
)
"""

#path_data = "C:\cda\Code\pyRSAM\data\tmp\CSIC\LaPalma\Geophone 0\X"
path_data = '.\data\CSIC_LaPalma_Geophone 0_X'
sonify_input(
    path_data=path_data,
    format_in='PICKLE',
    starttime=UTCDateTime(2021, 11, 30, 0, 0),
    endtime=UTCDateTime(2021, 11, 30, 23, 59),
    freqmin=20/200,
    freqmax=20000/200,
    speed_up_factor=200,
    fps=10,  # Use fps=60 to ~recreate the JHEPC entry (slow to save!)
    spec_win_dur=8,
    db_lim='smart',
)

