# Installation
- Install miniconda
- Install Pycharm Community
- Clone or download project from https://github.com/cda-gti-upm/pyRSAM.git
- Create virtual environment and install packages: `conda env create -f environment.yml`

# Preparing data
- Copy the folder with all seismic data files inside the project in the data directory.

# Read seismic data files and preprocessing
- `preprocessing.py`: preprocess seismic data files. Read all the original files in SEG2 format from a given directory 
and creates a new hierarchy of folders and files according to the network, station, location, channel, and information. 
Optionally, the sensor response is corrected.
- `store_data_per_period.py`: reads datafiles of a specific location (geophone) and channel from a directory and save 
them in large size # files to speed up posterior data loading. The size is determined by the specified data time interval.

# Plot seismic data (time plot)
- `plot_seismic_data.py`: plot seismic data. Read datafiles of a specific location (geophone) and channel and plot 
seismic data (standard plot and a day plot). If flag variable `f_plot_datafiles = True`, a time plot figure is saved per 
acquisition file.

# Plot spectrograms
- `plot_spectrograms_per_file.py`: plot spectrogram per data file. Script that reads datafiles of a specific location
(geophone) and channel from a directory and computes a spectogram per data file using librosa library. Spectrogram plots
are saved in independent image files.
- `plot_spectrograms_per_period.py`: plot spectrograms per time intervals. Script that reads datafiles of a specific 
location (geophone) and channel from a directory and computes a spectrogram per specified interval of time using librosa
library. Spectrogram plots are saved in independent image files.