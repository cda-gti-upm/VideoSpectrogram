# Installation
Clone the repository to download the code
`git clone https://github.com/cda-gti-upm/VideoSpectrogram.git`

The Python version must be python 3.11.

Install the following elements by writting this in the terminal:
- pip install obspy==1.4.0
- pip install librosa==0.10.1
- pip install pandas==2.1.4
- pip install tqdm==4.65.0
- pip install psutil==5.9.8

Additionally, [ffmpeg](https://www.ffmpeg.org/download.html) should be installed for generating videos and audios of spectrograms using sonify. Follow 
the instructions from this [link](https://phoenixnap.com/kb/ffmpeg-windows) to add  puffmgeg to the system path.

# Processing
From command line, execute:
`python generate_audio_video.py`

To specify input data and parameters related to the generated video, edit `generate_audio_video.py`