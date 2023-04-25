# https://docs.obspy.org/tutorial/code_snippets/waveform_plotting_tutorial.html
# Plot parameters: https://docs.obspy.org/packages/autogen/obspy.core.stream.Stream.plot.html#obspy.core.stream.Stream.plot

from obspy.core import read
import matplotlib.pyplot as plt

singlechannel = read('https://examples.obspy.org/COP.BHZ.DK.2009.050')
print(singlechannel)
threechannels = read('https://examples.obspy.org/COP.BHE.DK.2009.050')
threechannels += read('https://examples.obspy.org/COP.BHN.DK.2009.050')
threechannels += read('https://examples.obspy.org/COP.BHZ.DK.2009.050')
print(threechannels)

# Basic plot
singlechannel.plot()

# Modifying size
singlechannel.plot(size=(1600, 500)) # Default: 800x250

# Customized Plots
dt = singlechannel[0].stats.starttime
singlechannel.plot(color='red', tick_rotation=5, tick_format='%I:%M %p',
                   starttime=dt + 60*60, endtime=dt + 60*60 + 120)

# Saving Plot to File
singlechannel.plot(outfile='singlechannel.png')

# Plotting multiple Channels
threechannels.plot(size=(800, 600))

# Creating a One-Day Plot
singlechannel.plot(type='dayplot')  # Default size: 800x600

# Event information
st = read("https://examples.obspy.org/GR.BFO..LHZ.2012.108")
st.filter("lowpass", freq=0.1, corners=2)
st.plot(type="dayplot", interval=60, right_vertical_labels=False,
        vertical_scaling_range=5e3, one_tick_per_line=True,
        color=['k', 'r', 'b', 'g'], show_y_UTC_label=False,
        events={'min_magnitude': 6.5})

# Plotting a Record Section
#stream.plot(type='section')

# Custom Plotting using Matplotlib
st = read()
tr = st[0]

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.plot(tr.times("matplotlib"), tr.data, "b-")
ax.xaxis_date()
fig.autofmt_xdate()
plt.show()