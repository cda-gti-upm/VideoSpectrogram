# Installation [TODO]
- Install miniconda
- Install Pycharm Community or Professional
- Clone or download project from https://github.com/cda-gti-upm/pyRSAM.git
- Create virtual environment and install packages: `conda env create -f environment.yml`

# Processing steps
- Prepare acquired data
- Plot seismic data and RSAM
- Plot Short-Term Spectrogram
- Plot Long-Term Spectrogram (LTSA)

The following sections describes how to execute the previous processing steps. For illustration purposes, it is assumed
that the seismic data (related to the volcano eruption in La Palma in September 19th, 2021) acquired by the array of 
geophones is stored in the folder `data/LaPalma`, which is composed by a series of dat files in format SEG2. 


# Prepare acquired data
Prepare geophone acquired data for further processing (such as plotting seismic data, spectrograms, LTSA, etc.).

Execute from the terminal: 
`data_preprocessing01.bat` 

Or alternatively: `python data_preprocessing.py configurations/preprocessingLaPalma.yaml`.

The parameters used in the script `data_preprocessing.py` are specified in the text-like configuration file 
`configurations/preprocessingLaPalma.yaml`. This file contains the following parameters:
- Paths for the input acquired data from the geophones (`path_data`) and for the output preprocessed data
(`path_output`).
```
# Data path
paths:
  path_data: ./data/LaPalma/  # Path to input datafiles
  path_output: ./results    # Path for output data (results)
```
- Data information about the seismic `network` and `station` of the acquired data.
```
# Data information
data_info:
  network: CSIC
  station: LaPalma
```
- xxx
```
# Sensor correction
sensor_correction:
  correc_f: True  # Correction flag
  # Sensor correction parameters: coefficients of the numerator and denominator of the transfer function
  b: [1.0000, -1.5365, 0.6507]   # Numerator
  a: [-1.0000, 1.9388, -0.9388]  # Denominator
```
- xxx
```
# Demean data trend
filter:
  demean_f: True
```
- xxx
```
# Time interval of data
time_interval: 86400  # Length in seconds. Example: 86400 seconds is one day.
```
- xxx
```
# Verbosing
verbose: True
```
- xxx
```
# Data format
data_format:
  format_in: SEG2        # Format of input datafiles
  format_out: PICKLE  # Format of output datafiles
```

# Plot seismic data and RSAM
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