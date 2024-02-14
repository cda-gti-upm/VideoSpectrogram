"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""
import math
import librosa.display
import sys
from obspy.core import UTCDateTime
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, ctx, State
from ltsa.ltsa import seismicLTSA
from threading import Timer
import os
import signal
import pyautogui
from seismic_dash_utils import read_and_preprocessing, open_browser, generate_title, update_layout, prepare_rsam, max_per_window
import socket
import plotly.graph_objs as go


def prepare_spectrogram(tr, s_min, s_max):

    """
        Computation of the spectrogram and generation of the figure. If the number of samples of the spectrogram is
        greater than 100 times the horizontal resolution of the screen (default 1920), the LTSA is computed. If not, a
        standard spectrogram.
    """
    print(f'Preparing figure...')
    print('Updating dates...')
    res = 1920
    num_samples = math.ceil(len(tr.data) / hop_length)
    if num_samples > (res * 100):
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
    title = generate_title(tr, 'Spectrogram')
    fig = px.imshow(S_db, x=time_abs, y=freqs, origin='lower',
                    labels={'y': 'Frequency (Hz)', 'color': 'Power (dB)'},
                    color_continuous_scale='jet', zmin=s_min, zmax=s_max)
    fig['layout']['yaxis']['autorange'] = False
    fig['layout']['yaxis']['range'] = [5, 125]
    fig['layout']['title'] = {'font': {'size': 13}, 'text': title, 'x': 0.5, 'yanchor': 'top'}
    fig['layout']['margin'] = {'t': 30, 'b': 30}
    fig['layout']['xaxis']['automargin'] = False

    return fig


# Get arguments
args = sys.argv
print(args)
geophone = args[1]
initial_channel = args[2]
start = args[3]
end = args[4]
filt_50Hz = args[5]
format_in = args[6]
location = args[7]
win_length = int(args[8])
hop_length = int(args[9])
n_fft = int(args[10])
window = args[11]
S_max = int(args[12])
S_min = int(args[13])

# Get a random free port
sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock

oversampling_factor = 25  # The higher, the more samples in the amplitude figure

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


path_root = './data/CSIC_LaPalma'
data_path = path_root + '_' + geophone + '_' + initial_channel

TR = read_and_preprocessing(data_path, format_in, starttime, endtime, filter_50Hz_f)

starttime = TR.stats.starttime
endtime = TR.stats.endtime

fig2 = prepare_spectrogram(TR, 75, 130)
trace = TR.copy()
num_samples = len(trace)
target_num_samples = 1920
factor = int(num_samples / (target_num_samples * oversampling_factor))
max_per_window(trace, factor)  # Change the representation before computing RSAM
fig1 = prepare_rsam(trace)
if len(trace) != 0:
    layout = update_layout(fig1['layout'], None, None, ['autorange'], fig1)
    fig1['layout'] = layout
del trace

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
         html.Button('Read new data', id='update', n_clicks=0),
         '  ',
         html.Button('Export in SVG', id='export', n_clicks=0),
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
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max',
                          type='number',
                          value=0,
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
    Output('startdate', 'value'),
    Output('enddate', 'value'),
    State('channel_selector', 'value'),
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
    Input('export', 'n_clicks'),
    State('geophone_selector', 'value'),
    Input('update', 'n_clicks'),
    Input('Smin', 'value'),
    Input('Smax', 'value'),
    State('time_plot', 'figure'),
    State('spectrogram', 'figure')
)
def update(channel_selector, startdate, enddate, relayoutdata_1, relayoutdata_2, max_y, min_y, max_freq,
           min_freq, auto_y, button, esport_button, geo_sel, update, s_min, s_max, fig_1, fig_2):
    print(f'El trigger es {ctx.triggered_id}')
    global TR
    global initial_channel
    global geophone
    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)
    if ctx.triggered_id == 'kill_button':
        # Close the app
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

    if ctx.triggered_id == 'export':
        if not os.path.exists("./exports"):
            os.mkdir("./exports")

        fig1 = go.Figure(data=fig_1['data'], layout=fig_1['layout'])
        file_title = fig1['layout']['title']['text']
        fig1.write_image(file=f"./exports/{file_title}.svg", format="svg", width=1920, height=1080, scale=1)
        fig2 = go.Figure(data=fig_2['data'], layout=fig_2['layout'])
        file_title = fig2['layout']['title']['text']
        fig2.write_image(file=f"./exports/{file_title}.svg", format="svg", width=3840, height=2160, scale=1)
        print('Export completed.')

    if ctx.triggered_id == 'update':
        if channel_selector != initial_channel or geo_sel != geophone:  # Read new data only if a parameter is changed
            # Read new data
            initial_channel = channel_selector
            geophone = geo_sel
            TR.data = np.zeros(len(TR))
            path = path_root + '_' + geo_sel + '_' + channel_selector
            TR = read_and_preprocessing(path, format_in, start_time, end_time, filter_50Hz_f)
            tr = TR.slice(start_time, end_time)
            fig_2 = prepare_spectrogram(tr=tr, s_min=s_min, s_max=s_max)
            target_num_samples = 1920
            factor = int(num_samples / (target_num_samples * oversampling_factor))
            max_per_window(tr, factor)
            fig_1 = prepare_rsam(tr)
            fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
            start_time = TR.stats.starttime
            end_time = TR.stats.endtime
            if len(tr) != 0:
                layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
                fig_1['layout'] = layout


    else:
        if ctx.triggered_id in ['time_plot']:
            if "xaxis.range[0]" in relayoutdata_1:
                # Get start and end time the user selected on the amplitude plot
                start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
                end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])

        if ctx.triggered_id in ['spectrogram']:
            if "xaxis.range[0]" in relayoutdata_2:
                # Get start and end time the user selected on the spectrogram
                start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
                end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])

        tr = TR.slice(start_time, end_time)

        if ctx.triggered_id in ['max', 'min', 'auto']:
            # Manage amplitude axis of the amplitude plot
            layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
            fig_1['layout'] = layout
        elif ctx.triggered_id in ['max_freq', 'min_freq']:
            # Maximum and minimum displayed frequencies
            fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
        elif ctx.triggered_id in ['Smax', 'Smin']:
            # Maximum and minimum displayed spectrogram power values
            fig_2['layout']['coloraxis']['cmax'] = s_max
            fig_2['layout']['coloraxis']['cmin'] = s_min

        if ctx.triggered_id not in ['max', 'min', 'auto', 'max_freq', 'min_freq', 'Smax', 'Smin', 'export', None]:
            fig_2 = prepare_spectrogram(tr=tr, s_min=s_min, s_max=s_max)
            target_num_samples = 1920
            factor = int(num_samples / (target_num_samples * oversampling_factor))
            max_per_window(tr, factor)
            fig_1 = prepare_rsam(tr)
            fig_2['layout']['yaxis']['range'] = [min_freq, max_freq]
            start_time = TR.stats.starttime
            end_time = TR.stats.endtime
            if len(tr) != 0:
                layout = update_layout(fig_1['layout'], min_y, max_y, auto_y, fig_1)
                fig_1['layout'] = layout

    return fig_1, fig_2, {'autosize': True}, {'autosize': True}, start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S")


# Run the app
Timer(5, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)


