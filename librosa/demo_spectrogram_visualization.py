# Using display.specshow
# https://librosa.org/doc/main/auto_examples/plot_display.html#sphx-glr-download-auto-examples-plot-display-py
# Full list of parameters
# https://librosa.org/doc/main/generated/librosa.display.specshow.html#librosa.display.specshow


import numpy as np
import matplotlib.pyplot as plt
import librosa


# Spectogram computation from example data.
# - Magnitudes to a decibel scale
y, sr = librosa.load(librosa.ex('trumpet'))
D = librosa.stft(y)  # STFT of y
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)


# Visualization using pyplot interface
plt.figure()
librosa.display.specshow(S_db)
plt.colorbar()
plt.show()


# Visualization using object-oriented interface
fig, ax = plt.subplots()
img = librosa.display.specshow(S_db, ax=ax)
fig.colorbar(img, ax=ax)
plt.show()


# Decorating your plot (object-oriented interface): title, axis names, colorbar formatting
fig, ax = plt.subplots()
img = librosa.display.specshow(S_db, x_axis='time', y_axis='linear', ax=ax)
ax.set(title='Now with labeled axes!')
fig.colorbar(img, ax=ax, format="%+2.f dB")
plt.show()


# Changing axis scales (object-oriented interface): logarithmic frequency axis
fig, ax = plt.subplots()
img = librosa.display.specshow(S_db, x_axis='time', y_axis='log', ax=ax)
ax.set(title='Using a logarithmic frequency axis')
fig.colorbar(img, ax=ax, format="%+2.f dB")
plt.show()


# Changing the analysis parameters (object-oriented interface)
# Default parameter settings used by librosa: sr=22050, hop_length=512, etc
fig, ax = plt.subplots()
D_highres = librosa.stft(y, hop_length=256, n_fft=4096)
S_db_hr = librosa.amplitude_to_db(np.abs(D_highres), ref=np.max)
img = librosa.display.specshow(S_db_hr, hop_length=256, x_axis='time', y_axis='log', ax=ax)
ax.set(title='Higher time and frequency resolution')
fig.colorbar(img, ax=ax, format="%+2.f dB")
plt.show()


# Color maps
# Gray colormap
fig, ax = plt.subplots()
img = librosa.display.specshow(S_db, cmap='gray_r', y_axis='log', x_axis='time', ax=ax)
ax.set(title='Inverted grayscale')
fig.colorbar(img, ax=ax, format="%+2.f dB")
plt.show()
# Jet colormap
fig, ax = plt.subplots()
img = librosa.display.specshow(S_db, cmap='jet', y_axis='log', x_axis='time', ax=ax)
ax.set(title='Jet colormap')
fig.colorbar(img, ax=ax, format="%+2.f dB")
plt.show()


# Multiple synchronized plots
# Construct a subplot grid with 3 rows and 1 column, sharing the x-axis)
fig, ax = plt.subplots(nrows=3, ncols=1, sharex=True)
# On the first subplot, show the original spectrogram
img1 = librosa.display.specshow(S_db, x_axis='time', y_axis='log', ax=ax[0])
ax[0].set(title='STFT (log scale)')
# On the second subplot, show the mel spectrogram
M = librosa.feature.melspectrogram(y=y, sr=sr)
M_db = librosa.power_to_db(M, ref=np.max)
img2 = librosa.display.specshow(M_db, x_axis='time', y_axis='mel', ax=ax[1])
ax[1].set(title='Mel')
# On the third subplot, show the chroma features
chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
img3 = librosa.display.specshow(chroma, x_axis='time', y_axis='chroma', key='Eb:maj', ax=ax[2])
ax[2].set(title='Chroma')
# To eliminate redundant axis labels, we'll use "label_outer" on all subplots:
for ax_i in ax:
    ax_i.label_outer()
# And we can share colorbars:
fig.colorbar(img1, ax=[ax[0], ax[1]])
# Or have individual colorbars:
fig.colorbar(img3, ax=[ax[2]])
plt.show()
# We can then even do fancy things like zoom into a particular time and frequency
# region.  Since the axes are shared, this will apply to all three subplots at once.
#ax[0].set(xlim=[1, 3])  # Zoom to seconds 1-3


'''
# Non-spectral data: covariance
R = librosa.segment.recurrence_matrix(y, mode='affinity')
fig, ax = plt.subplots()
img = librosa.display.specshow(R, y_axis='time', x_axis='time', ax=ax)
ax.set(title='Recurrence / self-similarity')
fig.colorbar(img, ax=ax)
plt.show()


# Non-spectral data: self-similarity
ccov = np.cov(y)
fig, ax = plt.subplots()
img = librosa.display.specshow(ccov, y_axis='chroma', x_axis='chroma', key='Eb:maj', ax=ax)
ax.set(title='Covariance')
fig.colorbar(img, ax=ax)
'''

