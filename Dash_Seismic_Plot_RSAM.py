"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""

import obspy
from obspy.core import UTCDateTime
import obspy.signal.filter
from utils import read_data_from_folder
from scipy.ndimage import uniform_filter1d
import plotly.express as px
import pandas as pd
from screeninfo import get_monitors
from dash import Dash, dcc, html, Input, Output, State, ctx
import sys


"""
Functions
"""


def read_and_preprocessing(path, in_format, start, end):

    # Read data
    print(f'Reading data ...')
    stream = read_data_from_folder(path, in_format, start, end)

    # Sort data
    print(f'Sorting data ...')
    stream.sort(['starttime'])
    print(f'Data spans from {stream[0].stats.starttime} until {stream[-1].stats.endtime}')

    # Merge traces
    print(f'Merging data ...')
    stream.merge(method=0, fill_value=0)
    trace = stream[0]

    # Filtering 50 Hz
    if filter_50Hz_f:
        print(f'Filtering 50 Hz signal ...')
        trace.data = obspy.signal.filter.bandstop(trace.data, 49, 51, trace.meta.sampling_rate, corners=8, zerophase=True)

    return trace


def generate_title(tr, prefix_name):
    title = f'{prefix_name} {tr.meta.network}, {tr.meta.station}, {tr.meta.location}, Channel {tr.meta.channel} '
    f'from {tr.stats.starttime.strftime("%d-%b-%Y at %H.%M.%S")} '
    f'until {tr.stats.endtime.strftime("%d-%b-%Y at %H.%M.%S")}'
    return title


def prepare_fig(tr, prefix_name):
    print(f'Preparing figure...')
    print('Updating dates...')
    # Decimation
    print(f'Decimation...')
    num_samples = len(tr.data)
    print(f'{prefix_name} trace has {len(tr.data)} samples...')
    n_pixels = []
    for m in get_monitors():
        n_pixels.append(m.width)

    target_num_samples = max(n_pixels)
    print(f'Monitor horizontal resolution is {target_num_samples} pixels')
    oversampling_factor = 25
    factor = int(num_samples / (target_num_samples * oversampling_factor))
    if factor > 1:
        tr.decimate(factor, no_filter=True)
        print(f'{prefix_name} trace reduced to {len(tr.data)} samples...')
    # Plotting and formatting
    print(f'Plotting and formating {prefix_name}...')
    df = pd.DataFrame({'data': tr.data, 'times': tr.times('utcdatetime')})  # check for problems with date format
    xlabel = "Date"
    ylabel = "Amplitude"
    title = generate_title(tr, prefix_name)

    fig = px.line(df, x="times", y="data", title='', labels={'times': xlabel, 'data': ylabel})
    fig['layout']['title'] = {'text': title, 'x': 0.5}
    fig['layout']['yaxis']['autorange'] = True
    return fig


def update_layout(layout, min_y, max_y, auto_y):
    if ((auto_y in [['Amplitude autorange'], ['RSAM autorange']]) or (min_y is None)) or (max_y is None):
        layout['yaxis']['autorange'] = True
    else:
        print('HOLA')
        layout['yaxis']['autorange'] = False
        layout['yaxis']['range'] = [min_y, max_y]
    return layout


args = sys.argv
geophone = args[1]
initial_channel = args[2]
start = args[3]
end = args[4]
filt_50Hz = args[5]
format_in = args[6]
print(args)

ST = obspy.Stream([obspy.Trace(), obspy.Trace(), obspy.Trace()])
ST_RSAM = ST.copy()
channels = ['X', 'Y', 'Z']

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}
path_root = './data/CSIC_LaPalma'

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
    TR = read_and_preprocessing(data_path, format_in, starttime, endtime)
    # Computes RSAM
    TR_RSAM = TR.copy()
    n_samples = int(TR_RSAM.meta.sampling_rate * 60 * 10)  # Amount to 10 minutes
    TR_RSAM.data = uniform_filter1d(abs(TR_RSAM.data), size=n_samples)

    ST[i] = TR
    ST_RSAM[i] = TR_RSAM

del TR
del TR_RSAM
starttime = ST[0].stats.starttime
endtime = ST[0].stats.endtime
TIME_TR = ST[0].slice(starttime, endtime)
RSAM_TR = ST_RSAM[0].slice(starttime, endtime)
fig1 = prepare_fig(TIME_TR, 'Plot')
fig2 = prepare_fig(RSAM_TR, 'RSAM')
del TIME_TR
del RSAM_TR
# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
    dcc.Dropdown(['Geophone1','Geophone2','Geophone3','Geophone4','Geophone5','Geophone6','Geophone7','Geophone8'],id='geophone_selector', value=geophone),
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
            style={'display': 'inline-block'})]
    ),

    html.Div(
        ['Start and end time (format: yyyy-mm-dd hh:mm:ss) ',
         dcc.Input(
             id='startdate',
             type='text',
             value=starttime.strftime("%Y-%m-%d %H:%M:%S"),
             style={'display': 'inline-block'},
             debounce=True
         ),
         dcc.Input(
             id='enddate',
             type='text',
             value=endtime.strftime("%Y-%m-%d %H:%M:%S"),
             debounce=True,
             style={'display': 'inline-block'})]
    ),
    html.Div([
        html.Div(
        [dcc.Checklist(id='auto', options=['Amplitude autorange'], value=['Amplitude autorange']),
         html.Div('Amplitude range (min to max):'),
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
        style={'display': 'in-line-block'}),
    html.Div(
        [dcc.Checklist(id='auto_RSAM', options=['RSAM autorange'], value=['RSAM autorange']),
         html.Div('RSAM range (min to max):'),
         dcc.Input(
             id='min_RSAM',
             type='number',
             value=None,
             debounce=True

         ),
         dcc.Input(
             id='max_RSAM',
             type='number',
             value=None,
             debounce=True
             )],
        style={'display': 'inline-block'})],
        style={'display': 'flex'}),

    dcc.Graph(id='time_plot', figure=fig1),


    dcc.Graph(id='RSAM', figure=fig2)
])



@app.callback(
    Output('time_plot', 'figure'),
    Output('RSAM', 'figure'),
    Input('channel_selector', 'value'),
    Input('startdate', 'value'),
    Input('enddate', 'value'),
    Input('time_plot', 'relayoutData'),
    Input('RSAM', 'relayoutData'),
    Input('max', 'value'),
    Input('min', 'value'),
    Input('max_RSAM', 'value'),
    Input('min_RSAM', 'value'),
    Input('auto', 'value'),
    Input('auto_RSAM', 'value'),
    Input('geophone_selector', 'value'),
    State('time_plot', 'figure'),
    State('RSAM', 'figure'),
    prevent_initial_call=True)
def update_plot(channel_selector, startdate, enddate, relayoutdata_1, relayoutdata_2, max_y, min_y, max_y_rsam,
                min_y_rsam, auto_y, auto_y_rsam, geo_sel, fig_1, fig_2):
    if ctx.triggered_id == 'geophone_selector':
        for j in range(0, 3):
            path = path_root + '_' + geo_sel + '_' + channels[j]
            print(path)
            tr = read_and_preprocessing(path, format_in, starttime, endtime)
            # Computes RSAM
            tr_rsam = tr.copy()
            n_samp = int(tr_rsam.meta.sampling_rate * 60 * 10)  # Amount to 10 minutes
            tr_rsam.data = uniform_filter1d(abs(tr_rsam.data), size=n_samp)
            ST[j] = tr
            ST_RSAM[j] = tr_rsam
        del tr
        del tr_rsam
    if channel_selector == 'X':
        trace = ST[0]
        trace_rsam = ST_RSAM[0]
    elif channel_selector == 'Y':
        trace = ST[1]
        trace_rsam = ST_RSAM[1]
    else:
        trace = ST[2]
        trace_rsam = ST_RSAM[2]
    start_time = UTCDateTime(startdate)
    end_time = UTCDateTime(enddate)

    if ctx.triggered_id in ['time_plot', 'channel_selector']:
        if "xaxis.range[0]" in relayoutdata_1:
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])

    if ctx.triggered_id in ['RSAM', 'channel_selector']:
        if "xaxis.range[0]" in relayoutdata_2:
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])

    time_tr = trace.slice(start_time, end_time)
    rsam_tr = trace_rsam.slice(start_time, end_time)

    if ctx.triggered_id in ['max', 'min', 'max_RSAM', 'min_RSAM', 'auto', 'auto_RSAM']:

        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y)
        fig_1['layout'] = layout
        layout_rsam = update_layout(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
        fig_2['layout'] = layout_rsam

    else:
        fig_1 = prepare_fig(tr=time_tr, prefix_name='Measured amplitude')
        fig_2 = prepare_fig(tr=rsam_tr, prefix_name='RSAM')
        layout = update_layout(fig_1['layout'], min_y, max_y, auto_y)
        fig_1['layout'] = layout
        layout_rsam = update_layout(fig_2['layout'], min_y_rsam, max_y_rsam, auto_y_rsam)
        fig_2['layout'] = layout_rsam

    return fig_1, fig_2


# Main program
# Run the app
app.run(debug=False)


