"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""
import math
import librosa.display
import sys
import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
from utils import read_data_from_folder
import numpy as np
import plotly.express as px
import pandas as pd
from screeninfo import get_monitors
from dash import Dash, dcc, html, Input, Output, ctx, State
from ltsa.ltsa import seismicLTSA
import webbrowser
from threading import Timer
import os
import signal
import pyautogui
from seismic_dash_utils import read_and_preprocessing, open_browser, generate_title, prepare_time_plot, update_layout
import socket
"""
Functions
"""

'''
def av_signal(tr, factor):
    length = len(tr)
    interval_length = round(length/factor)
    n_intervals = math.ceil(length/interval_length)
    tr_s = obspy.core.Trace(data=np.arange(0,n_intervals))
    
    for i in range(0, n_intervals-1):
        avg = 0
        for j in range(i*interval_length, i*interval_length + interval_length):
            avg += tr.data(j)
        
        avg = avg / interval_length
        tr_s.data[i] = avg
'''

def prepare_spectrogram(trace, start_time, end_time, s_min, s_max):
    print(f'Preparing figure...')
    print('Updating dates...')
    tr = trace.slice(start_time, end_time)
    res = 1920
    num_samples = math.ceil(len(tr.data) / hop_length)
    if num_samples > (res * 10):
        print('COMPUTATION OF LTSA')
        d = seismicLTSA(tr.data, tr.meta.sampling_rate)
        params = {'div_len': int(np.round(len(tr.data) / res)),  # Length in numer of samples
                  'subdiv_len': win_length,
                  'nfft': n_fft,
                  'noverlap': hop_length}
        d.set_params(params)

        # compute the LTSA -- identical to s.compute()
        d.compute(ref=1, amin=1e-5, top_db=None)
        S_db = d.ltsa
        frame_indices = np.arange(S_db.shape[1])
        time_rel = (np.asanyarray(frame_indices) * d.div_len + (d.div_len / 2)).astype(int) / float(
            tr.meta.sampling_rate)
        freqs = np.arange(0, n_fft / 2) * tr.meta.sampling_rate / n_fft

    else:
        print('COMPUTATION OF COMPLETE SPECTROGRAM')
        d = librosa.stft(tr.data, hop_length=hop_length, n_fft=n_fft, win_length=win_length, window=window, center=True)
        S_db = librosa.amplitude_to_db(np.abs(d), ref=1, amin=1e-5, top_db=None)
        frame_indices = np.arange(d.shape[1])
        time_rel = librosa.frames_to_time(frame_indices, sr=tr.meta.sampling_rate, hop_length=hop_length, n_fft=None)
        freqs = np.arange(0, 1 + n_fft / 2) * tr.meta.sampling_rate / n_fft

    time_abs = list([tr.stats.starttime + time_rel[0]])
    time_abs[0] = tr.stats.starttime + time_rel[0]
    for i in range(1, len(time_rel)):
        time_abs.append(tr.stats.starttime + time_rel[i])
    title = generate_title(trace, 'Spectrogram')
    fig = px.imshow(S_db, x=time_abs, y=freqs, origin='lower',
                    labels={'x': 'Time', 'y': 'Frequency (Hz)', 'color': 'Power (dB)'},
                    color_continuous_scale='jet', zmin=s_min, zmax=s_max)
    fig['layout']['yaxis']['autorange'] = False
    fig['layout']['yaxis']['range'] = [5, 125]
    fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
    fig['layout']['margin'] = {'t': 30, 'b': 30}
    fig['layout']['xaxis']['automargin'] = False

    return fig


ST = obspy.Stream([obspy.Trace(), obspy.Trace(), obspy.Trace()])
channels = ['X', 'Y', 'Z']

args = sys.argv
print(args)
geophone = args[1]
initial_channel = args[2]
start = args[3]
end = args[4]
filt_50Hz = args[5]
format_in = args[6]
win_length = int(args[7])
hop_length = int(args[8])
n_fft = int(args[9])
window = args[10]
S_max = int(args[11])
S_min = int(args[12])
path_root = './data/CSIC_LaPalma'

oversampling_factor = 10

sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock

if start:
    starttime = UTCDateTime(start)
else:
    starttime = None

if end:
    endtime = UTCDateTime(end)
else:
    endtime = None

if filt_50Hz == 's':
    filter_50Hz_f = True
else:
    filter_50Hz_f = False

for i in range(0, 3):
    data_path = path_root + '_' + geophone + '_' + channels[i]
    print(data_path)
    TR = read_and_preprocessing(data_path, format_in, starttime, endtime, filter_50Hz_f)
    ST[i] = TR

del TR
starttime = ST[0].stats.starttime
endtime = ST[0].stats.endtime
TR = ST[0].slice(starttime, endtime)
fig1 = prepare_time_plot(TR, oversampling_factor)
fig2 = prepare_spectrogram(TR, starttime, endtime, s_min=75, s_max=130)

del TR

# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
    dcc.Dropdown(
        ['Geophone1', 'Geophone2', 'Geophone3', 'Geophone4', 'Geophone5', 'Geophone6', 'Geophone7', 'Geophone8'],
        id='geophone_selector', value=geophone),
    html.Div(
        ['Channel: ',
         dcc.RadioItems(
             id='channel_selector',
             options=[
                 {'label': 'Channel X   ', 'value': 'X'},
                 {'label': 'Channel Y   ', 'value': 'Y'},
                 {'label': 'Channel Z   ', 'value': 'Z'}
             ],
             value=initial_channel,
             style={'display': 'inline-block'})],
    ),
    html.Div(
        ['Start and end time (yyyy-mm-dd hh:mm:ss): ',
         dcc.Input(
             id='startdate',
             type='text',
             value=starttime.strftime("%Y-%m-%d %H:%M:%S"),
             debounce=True,
             style={'display': 'inline-block'}
         ),
         dcc.Input(
             id='enddate',
             type='text',
             value=endtime.strftime("%Y-%m-%d %H:%M:%S"),
             debounce=True,
             style={'display': 'inline-block'}),
         '  ',
         html.Button('Close app', id='kill_button', n_clicks=0)],
    ),

    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto', options=['autorange'], value=['autorange']),
                      html.Div('Amplitude range (min to max)'),
                      dcc.Input(
                          id='min',
                          type='number',
                          value=None,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max',
                          type='number',
                          value=None,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[html.Br(),
                      html.Div('Spectrogram frequency range (Hz)'),
                      dcc.Input(
                          id='min_freq',
                          type='number',
                          value=5,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_freq',
                          type='number',
                          value=125,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[html.Br(),
                      html.Div('Spectrogram power range (dB)'),
                      dcc.Input(
                          id='Smin',
                          type='number',
                          value=75,
                          debounce=True
                      ),
                      dcc.Input(
                          id='Smax',
                          type='number',
                          value=130,
                          debounce=True
                      )],
            style={'display': 'in-line-block'})],
        style={'display': 'flex'}),

    dcc.Graph(id='time_plot', figure=fig1, style={'width': '164.5vh', 'height': '30vh'}),
    dcc.Graph(id='spectrogram', figure=fig2, style={'width': '170vh', 'height': '50vh'})
])


@app.callback(
    Output('time_plot', 'figure'),
    Output('spectrogram', 'figure'),
    Output('time_plot', 'relayoutData'),
    Output('spectrogram', 'relayoutData'),
    Input('channel_selector', 'value'),
    Input('startdate', 'value'),
    Input('enddate', 'value'),
    Input('time_plot', 'relayoutData'),
    Input('spectrogram', 'relayoutData'),
    Input('max', 'value'),
    Input('min', 'value'),
    Input('max_freq', 'value'),
    Input('min_freq', 'value'),
    Input('auto', 'value'),
    Input('kill_button', 'n_clicks'),
    Input('geophone_selector', 'value'),
    Input('Smin', 'value'),
    Input('Smax', 'value'),
    State('time_plot', 'figure'),
    State('spectrogram', 'figure')
)
def update(channel_selector, startdate, enddate, relayoutdata_1, relayoutdata_2, max_y, min_y, max_freq,
           min_freq, auto_y, button, geo_sel, s_min, s_max, fig_1, fig_2):
    print(f'El trigger es {ctx.triggered_id}')
    if ctx.triggered_id == 'kill_button':
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

    if ctx.triggered_id == 'geophone_selector':
        st_length = len(ST[0])
        ST[0].data = np.zeros(st_length)
        ST[1].data = np.zeros(st_length)
        ST[2].data = np.zeros(st_length)
        for j in range(0, 3):
            path = path_root + '_' + geo_sel + '_' + channels[j]
            print(path)
            tr = read_and_preprocessing(path, format_in, starttime, endtime, filter_50Hz_f)
            ST[j] = tr

        del tr

    if channel_selector == 'X':
        trace = ST[0]
    elif channel_selector == 'Y':
        trace = ST[1]
    else:
        trace = ST[2]

    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)

    if ctx.triggered_id in ['time_plot']:
        if "xaxis.range[0]" in relayoutdata_1:
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])

    if ctx.triggered_id in ['spectrogram']:
        if "xaxis.range[0]" in relayoutdata_2:
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])

    tr = trace.slice(start_time, end_time)
    tr_spec = tr.copy()

    if ctx.triggered_id in ['max', 'min', 'auto']:
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, tr, True)
        fig_1['layout'] = layout
    elif ctx.triggered_id in ['max_freq', 'min_freq']:
        fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
    elif ctx.triggered_id in ['Smax', 'Smin']:
        fig_2['layout']['coloraxis']['cmax'] = s_max
        fig_2['layout']['coloraxis']['cmin'] = s_min
    else:
        fig_1 = prepare_time_plot(tr=tr, oversampling_factor=oversampling_factor)
        fig_2 = prepare_spectrogram(trace=tr_spec, start_time=start_time, end_time=end_time, s_min=s_min, s_max=s_max)
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, tr, True)
        fig_1['layout'] = layout
        fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]

    return fig_1, fig_2, {'autosize': True}, {'autosize': True}


# Main program
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)


