# https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.slice.html#obspy.core.stream.Stream.slice

import obspy
from obspy.core import UTCDateTime

st = obspy.read()
print(st)

dt = UTCDateTime("2009-08-24T00:20:20")
st = st.slice(dt, dt + 5)
print(st)