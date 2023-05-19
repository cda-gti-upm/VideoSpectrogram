# Installation
- Install miniconda
- Install Pycharm Community
- Clone or download project from https://github.com/cda-gti-upm/pyRSAM.git
- Create virtual environment and install packages: `conda env create -f environment.yml`

# Preparing data
- Copy the folder with all seismic data files inside the project in the data directory.

# Read seismic data files and preprocessing
- Execute from terminal: `data_preprocessing01.bat` or alternatively `python data_preprocessing.py configurations/preprocessing01.yaml`.

# Plot seismic data (time plot)
- Execute from terminal: `plot_seismic_data_one_channel01.bat` or alternatively `python plot_seismic_data_one_channel.py configurations/plot_independent_channels_geophone_0.yaml` (several yaml configuration files can be used for the different geophones). 
- 

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