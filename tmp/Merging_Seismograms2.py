import os
import matplotlib.pyplot as plt
import numpy as np
import obspy
from obspy.core import UTCDateTime
import plotly.express as px


# Path to datafiles of one specific location (geophone) and channel
read_from_dir = False
path_data = './data/CSIC/LaPalma/Geophone_0/X/'
read_from_file = True
path_data = './data/CSIC_LaPalma_Geophone_0_X_sorted.pickle' # 'CSIC_LaPalma_Geophone_0_X_sorted_merged.pickle' './data/CSIC_LaPalma_Geophone_0_X_sorted.pickle'
verbose = True
merged_data = False
save_data_unsorted = False
filename_data_unsorted = 'CSIC_LaPalma_Geophone_0_X.pickle'
save_data_sorted = False
filename_data_sorted = 'CSIC_LaPalma_Geophone_0_X_sorted.pickle'
save_data_sorted_merged = False
filename_data_sorted_merged = 'CSIC_LaPalma_Geophone_0_X_sorted_merged.pickle'
# TODO: add starttime and endtime parameters

# Read in all data files from directory
if read_from_dir:
    dirlist = sorted(os.listdir(path_data))
    first_file = True
    for file in (os.path.join(path_data, file) for file in dirlist):
        if os.path.isfile(file):
            try:
                if first_file:
                    st = obspy.read(file, format='PICKLE', headonly=False)
                    first_file = False
                else:
                    st += obspy.read(file, format='PICKLE', headonly=False)
            except Exception:
                if verbose:
                    print("Can not read %s" % (file))


# Save data into pickle format
if save_data_unsorted:
    st.write('filename_data_unsorted', format='PICKLE')

if read_from_file:
    st = obspy.read(path_data, format='PICKLE', headonly=False)

# sort
if False:
    st.sort(['starttime'])
print(f'Data spans from {st[0].stats.starttime} until {st[-1].stats.endtime}')

# Save data into pickle format
if save_data_sorted:
    st.write('filename_data_sorted', format='PICKLE')

# use common reference time and have x-Axis as relative time in seconds.
t0 = st[0].stats.starttime

if True:
    startday = UTCDateTime("2021-11-23T00:00:00")
    endday = UTCDateTime("2021-11-28T00:00:00")
    delta_day = 24*60*60  # Day length in seconds
    for i in range(int(startday.timestamp), int(endday.timestamp), delta_day):
        st_day = st.copy()
        st_day = st_day.slice(UTCDateTime(i), UTCDateTime(i) + delta_day)
        st_day.sort(['starttime'])
        st_day.merge(method=1)
        if np.ma.isMaskedArray(st_day[0].data):
            st_day[0].data = st_day[0].data.filled()
        st_day.write(f'CSIC_LaPalma_Geophone_0_X_sorted_merged_{UTCDateTime(i).strftime("d%dm%my%y__H%H-M%MS%S")}.pickle', format='PICKLE')

#st_day.spectrogram(log=True, title=f'Spectrogram')

# Plot the first data series
if False:
    num_plots = 5
    fig, axes = plt.subplots(nrows=num_plots, sharex=True)
    ax = None
    for i, (tr, ax) in enumerate(zip(st, axes)):
        if i == num_plots:
            break
        ax.plot(tr.times(reftime=t0), tr.data)

    axes[-1].set_xlabel(f'seconds relative to {t0}')
    plt.show()

# Plot the first spectrograms
# TODO: Hacer el plot en un subplot
if False:
    num_plots = 5
    for i in range(5):
        st[i].spectrogram(log=True, title=f'{i}')

'''
fig, axes = plt.subplots(nrows=num_plots, sharex=True)
ax = None
for i, (tr, ax) in enumerate(zip(st, axes)):
    if i == num_plots:
        break
    ax.plot(tr.times(reftime=t0), tr.data)
'''

# Merge the data together and plot in a similar way in the bottom Axes
# TODO: revisar métodos de merge
if merged_data:
    st.merge(method=1)
    st[0].data = st[0].data.filled()
    if save_data_sorted_merged:
        st.write(filename_data_sorted_merged, format='PICKLE')

# Filter erroneous large values
ind = st[0].data > 1000000
st[0].data[ind] = 0

plt.figure
plt.plot(st[0].times(reftime=t0), st[0].data, 'r')
plt.xlabel(f'seconds relative to {t0}')
plt.show()

# Interactive plot
fig = px.line(x=st[0].times(reftime=t0), y=st[0].data)
fig.show()

# Day plot
st.plot(type='dayplot', interval=60, size=(800*4,600*4))


# TODO: Another option would be to plot absolute times by using ...
# Trace.times(type='matplotlib') and letting matplotlib know that x-Axis has
# absolute times, by using ax.xaxis_date() and fig.autofmt_xdate()

'''
for (tr, ax) in zip(st2, axes2):
    ax.plot(tr.times(type='matplotlib'), tr.data)
    ax.xaxis_date()
    fig2.autofmt_xdate()

# Merge the data together and plot in a similar way in the bottom Axes
st2.merge(method=1)
axes[-1].plot(st2[0].times(type='matplotlib'), st2[0].data, 'r')
axes[-1].set_xlabel(f'Absolute time')
ax.xaxis_date()
fig2.autofmt_xdate()
plt.show()
'''