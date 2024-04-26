from sonify.sonify import sonify
from obspy import UTCDateTime

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