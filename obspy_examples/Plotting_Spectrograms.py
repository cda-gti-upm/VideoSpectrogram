# Plotting spectrograms
# https://docs.obspy.org/tutorial/code_snippets/plotting_spectrograms.html
# https://docs.obspy.org/packages/autogen/obspy.imaging.spectrogram.spectrogram.html#obspy.imaging.spectrogram.spectrogram


import obspy


st = obspy.read("https://examples.obspy.org/RJOB_061005_072159.ehz.new")
# The spectrogram will on default have 90% overlap and a maximum sliding window size of 4096 points.
st.spectrogram(log=True, title='BW.RJOB ' + str(st[0].stats.starttime))