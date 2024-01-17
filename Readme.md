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
Execute from the terminal:`python seismic_ui.py`. Then the following prompt will appear:

![alt text](https://github.com/EnolAyo/pyRSAM/blob/master/pictures/primera.png)

You have to write the number corresponding to the option that you want to visualize and then press Enter.
Then you have to select the number of the geophone (1 to 8), the channel (X, Y, Z), and the earliest and latest time that you want to visualize data from. If you want to visualize all the available data, just press Enter without typing anything when the program asks you for start and end time.

![alt text](https://github.com/EnolAyo/pyRSAM/blob/master/pictures/parametros.png)

If the option 3 is selected (Time plot + Spectrogram), the progream will show some spectrogram-related parameters and its default value and ask you if you wish to modify them. Type 's' and press Enter if you want to modify thoose parameters, or type 'n' to use the default values.

![alt text](https://github.com/EnolAyo/pyRSAM/blob/master/pictures/parametros_espectrograma.png)

Then, the program starts to read the data. When it is ready, the browser will automatically be launched.

![alt text](https://github.com/EnolAyo/pyRSAM/blob/master/pictures/leyendo.png)

# Some considerations
It is recommended not to touch any input of the program when in the tab name appears 'Updating...'. Wait until it disappears before changing any parameter, specially when you change the geophone number.

![alt text](https://github.com/EnolAyo/pyRSAM/blob/master/pictures/update.png)

Finally, when you desire to close the program, press the button 'Close app'. If you do not do that and instead just close the browser, the program will still be running and you will have to kill it from the terminal.

![alt text](https://github.com/EnolAyo/pyRSAM/blob/master/pictures/cerrar.png)
