# Installation
The Python version must be python 3.11.
Install the following elements by writting this in the terminal:
- pip install obspy==1.4.0
- pip install librosa==0.10.1
- pip install dash==2.7.0
- pip install pandas==2.1.4
- pip install pyautogui==0.9.54
- pip install tqdm==4.65.0
- pip install pyfiglet==1.0.2
- pip install screeninfo==0.8.1
- pip install pyyaml==6.0.1

# Data preparation and preprocessing
Data from geophones should be in the project folder `.\data\LaPalma`
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
# Data visualization
Execute from the terminal:`python seismic_ui.py`.
