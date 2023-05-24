# Reading seismological data
print("Reading seismological data")
print("-----------------------------")
import obspy
from obspy import read
import matplotlib.pyplot as plt

st = read('./data/107790.dat')

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


channels = []
for i in range(len(st)):
    # UserWarning: Non-zero value found in Trace's 'DELAY' field.
    # This is not supported/tested yet and might lead to a wrong starttime
    # of the Trace. Please contact the ObsPy developers with a sample file.
    st[i].stats.seg2.DELAY = "0"
    st[i].meta.seg2.DELAY = "0"
    channels.append(obspy.Stream(traces=[st[i]]))

st = read('./data/107791.dat')
for i in range(len(st)):
    st[i].stats.seg2.DELAY = "0"
    st[i].meta.seg2.DELAY = "0"
    channels[i] += obspy.Stream(traces=[st[i]])
st = read('./data/107792.dat')
for i in range(len(st)):
    st[i].stats.seg2.DELAY = "0"
    st[i].meta.seg2.DELAY = "0"
    channels[i] += obspy.Stream(traces=[st[i]])

channels[0].sort(['starttime'])

# use common reference time and have x-Axis as relative time in seconds.
t0 = channels[0][0].stats.starttime

# Go through the stream object and plot the data with a shared x axis
fig, axes = plt.subplots(nrows=len(channels[0])+1, sharex=True)
ax = None

for (tr, ax) in zip(channels[0], axes):
    ax.plot(tr.times(reftime=t0), tr.data)

# Merge the data together and plot in a similar way in the bottom Axes
channels[0].merge(method=1)
axes[-1].plot(channels[0][0].times(reftime=t0), channels[0][0].data, 'r')
axes[-1].set_xlabel(f'seconds relative to {t0}')
plt.show()
