# Reading seismological data
print("Reading seismological data")
print("-----------------------------")
from obspy import read
st = read('http://examples.obspy.org/RJOB_061005_072159.ehz.new')
print("Stream:")
print(st)
len(st)
tr = st[0]  # assign first and only trace to new variable
print("Trace:")
print(tr)

# Accessing Meta Data
print("\nAccessing Meta Data")
print("-----------------------------")
print(tr.stats)
print(tr.stats.station)
print(tr.stats.gse2.datatype)

# Accessing Waveform Data
print("\nAccessing Waveform Data")
print("-----------------------------")
print(tr.data)
print(tr.data[0:3])
print(len(tr))

# Data Preview
print("\nData Preview")
print("-----------------------------")
st.plot()