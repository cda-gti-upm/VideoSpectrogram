"""
Save seismic data as an audio file
"""

import librosa
import soundfile as sf
import pyrubberband as pyrb
import obspy
import numpy as np
import matplotlib.pyplot as plt
import scipy

"""
import os
os.environ['NUMBA_DISABLE_INTEL_SVML'] = '1'
"""

"""
Arguments
"""
path_data = "C:/cda/Code/pyRSAM/data/LaPalma/115440.dat"
path_audio = "data/output.wav"
sample_rate = 250
resampling = 44100

# Format of input datafiles
format_in = 'SEG2'


"""
Read and normalize data
"""
# Read data file
st = obspy.read(path_data, format=format_in, headonly=False)
data = st[0].data

# Normalize data and resample
#data_norm = librosa.resample(data_norm, orig_sr=sample_rate, target_sr=resampling)
data_resampl = scipy.signal.resample(data, int(len(data)*resampling/sample_rate))
#data = librosa.util.normalize(data)
data_norm = (data_resampl-np.min(data))/(np.max(data_resampl)-np.min(data_resampl))
data_norm = data_norm * 2 - 1


""" Time intensity plot"""
fig, ax = plt.subplots(nrows=2, ncols=1, sharex=False, figsize=(18, 10), dpi=100)
fig.suptitle(f'Amplitud plot')

ax[0].plot(st[0].times(reftime=st[0].stats.starttime), data, 'k')
ax[0].set_xlabel(f'Time relative to {st[0].stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
ax[0].set_ylabel('Intensity')

ax[1].plot(data_norm, 'k')
ax[1].set_xlabel(f'Time relative to {st[0].stats.starttime.strftime("%d-%b-%Y at %H:%M:%S")}')
ax[1].set_ylabel('Intensity')

plt.show()

# To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
for ax_i in ax:
    ax_i.label_outer()


# Pitch shift
#data_shifted = librosa.effects.pitch_shift(data, sr=sample_rate, n_steps=4)
#data_shifted = pyrb.pitch_shift(data, sr=sample_rate, n_steps=4)


# Save audio file
sf.write(path_audio, data, sample_rate, subtype='PCM_16')
sf.write("data/output_resampl.wav", data_norm, resampling, subtype='PCM_16')

