"""
Plot seismic data: one plot per geophone and channel
Read datafiles of given locations (geophones) and channels and generate one independent plot for every
one.
"""

from obspy.core import UTCDateTime
from dash import Dash, dcc, html, Input, Output, ctx, State
import sys
from threading import Timer
import os
import signal
import pyautogui
import socket
from CSIC_Seismic_Visualizator_Utils import (open_browser, get_3_channel_figures, update_layout_3_channels,
                                             create_config)
import plotly.graph_objs as go
import time
from plotly.subplots import make_subplots

args = sys.argv
GEOPHONE = args[1]
start = args[2]
end = args[3]
filt_50Hz = args[4]
format_in = args[5]
location = args[6]
min_y_fig1 = float(args[7])
max_y_fig1 = float(args[8])
auto_y_fig1 = args[9]
min_y_fig2 = float(args[10])
max_y_fig2 = float(args[11])
auto_y_fig2 = args[12]
min_y_fig3 = float(args[13])
max_y_fig3 = float(args[14])
auto_y_fig3 = args[15]

OPTION = 2

oversampling_factor = 20
sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}
path_root = f'./data/CSIC_{location}'

try:
    if start:
        STARTTIME = UTCDateTime(start)
    else:
        STARTTIME = None

    if end:
        ENDTIME = UTCDateTime(end)
    else:
        ENDTIME = None
except Exception as e:
    print("Date is not valid. (%s: %s)" % (type(e).__name__, e))
    sys.exit()
if (STARTTIME is not None) and (ENDTIME is not None):
    if STARTTIME > ENDTIME:
        print('Start time is after end time.')
        sys.exit()

if filt_50Hz == 's':
    filter_50Hz_f = True
else:
    filter_50Hz_f = False

auto_y_fig1 = ['autorange'] if auto_y_fig1 == 'autorange' else []
auto_y_fig2 = ['autorange'] if auto_y_fig2 == 'autorange' else []
auto_y_fig3 = ['autorange'] if auto_y_fig3 == 'autorange' else []

[fig1, fig2, fig3, STARTTIME, ENDTIME] = get_3_channel_figures(STARTTIME, ENDTIME, GEOPHONE, filter_50Hz_f, path_root, oversampling_factor, format_in)


# Creating app layout:

app = Dash(__name__, title='Option 2')
app.layout = html.Div([
    dcc.Dropdown(['Geophone1', 'Geophone2', 'Geophone3', 'Geophone4',
                  'Geophone5', 'Geophone6', 'Geophone7', 'Geophone8'], id='geophone_selector', value=GEOPHONE),
    html.Div(
        ['Select the start and end time (format: yyyy-mm-dd hh:mm:ss): ',
         dcc.Input(
             id='startdate',
             type='text',
             value=STARTTIME.strftime("%Y-%m-%d %H:%M:%S.%f"),
             style={'display': 'inline-block'},
             debounce=True
         ),
         dcc.Input(
             id='enddate',
             type='text',
             value=ENDTIME.strftime("%Y-%m-%d %H:%M:%S.%f"),
             debounce=True,
             style={'display': 'inline-block'},),
         '  ',
         html.Button('Update data', id='update', n_clicks=0),
         '  ',
         html.Button('Export in SVG', id='export', n_clicks=0),
         '   ',
         html.Button('Close app', id='kill_button', n_clicks=0),
         '      ',
         dcc.Input(
             id='config_name',
             type='text',
             value='',
             debounce=True,
             style={'display': 'inline-block'}),
         html.Button('Save config.', id='save_config', n_clicks=0)
         ],
    ),
    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto_x', options=['autorange'], value=auto_y_fig1),
                      html.Div('Channel X amplitude range (min to max)'),
                      dcc.Input(
                          id='min_x',
                          type='number',
                          value=min_y_fig1,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_x',
                          type='number',
                          value=max_y_fig1,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_y', options=['autorange'], value=auto_y_fig2),
                      html.Div('Channel Y amplitude range (min to max)'),
                      dcc.Input(
                          id='min_y',
                          type='number',
                          value=min_y_fig2,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_y',
                          type='number',
                          value=max_y_fig2,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_z', options=['autorange'], value=auto_y_fig3),
                      html.Div('Channel Z amplitude range (min to max)'),
                      dcc.Input(
                          id='min_z',
                          type='number',
                          value=min_y_fig3,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_z',
                          type='number',
                          value=max_y_fig3,
                          debounce=True
                      )],
            style={'display': 'in-line-block'})],
        style={'display': 'flex'}),
    dcc.Graph(id='x_plot', figure=fig1, style={'width': '170vh', 'height': '25vh'}, relayoutData={'autosize': True}, config={'modeBarButtonsToRemove': ['pan2d', 'autoScale2d']}),
    dcc.Graph(id='y_plot', figure=fig2, style={'width': '170vh', 'height': '25vh'}, relayoutData={'autosize': True}, config={'modeBarButtonsToRemove': ['pan2d', 'autoScale2d']}),
    dcc.Graph(id='z_plot', figure=fig3, style={'width': '170vh', 'height': '25vh'}, relayoutData={'autosize': True}, config={'modeBarButtonsToRemove': ['pan2d', 'autoScale2d']})
])


@app.callback(
    Output('x_plot', 'figure'),
    Output('y_plot', 'figure'),
    Output('z_plot', 'figure'),
    Output('x_plot', 'relayoutData'),
    Output('y_plot', 'relayoutData'),
    Output('z_plot', 'relayoutData'),
    Output('startdate', 'value'),
    Output('enddate', 'value'),
    State('geophone_selector', 'value'),
    State('startdate', 'value'),
    State('enddate', 'value'),
    State('config_name', 'value'),
    Input('x_plot', 'relayoutData'),
    Input('y_plot', 'relayoutData'),
    Input('z_plot', 'relayoutData'),
    Input('max_x', 'value'),
    Input('min_x', 'value'),
    Input('max_y', 'value'),
    Input('min_y', 'value'),
    Input('max_z', 'value'),
    Input('min_z', 'value'),
    Input('auto_x', 'value'),
    Input('auto_y', 'value'),
    Input('auto_z', 'value'),
    Input('kill_button', 'n_clicks'),
    Input('update', 'n_clicks'),
    Input('export', 'n_clicks'),
    Input('save_config', 'n_clicks'),
    State('x_plot', 'figure'),
    State('y_plot', 'figure'),
    State('z_plot', 'figure'),
)
def update_plot(geo_sel, starttime_app, endtime_app, config_name, relayoutdata_1, relayoutdata_2, relayoutdata_3, max_x, min_x, max_y,
                min_y, max_z, min_z, auto_x, auto_y, auto_z, button, update, export_button, save, fig_1, fig_2, fig_3):

    global GEOPHONE
    ini_exec_time = time.time()

    try:
        start_time = UTCDateTime(starttime_app)
        end_time = UTCDateTime(endtime_app)
    except Exception as e_dates:
        start_time = UTCDateTime(fig_1['data'][0]['x'][0])
        end_time = UTCDateTime(fig_1['data'][0]['x'][-1])
        print(f'Dates are wrong: {e_dates}')
    if start_time > end_time:
        start_time = UTCDateTime(fig_1['data'][0]['x'][0])
        end_time = UTCDateTime(fig_1['data'][0]['x'][-1])
        print('No valid dates')

    if ctx.triggered_id == 'export':
        print('Saving figures...')
        if not os.path.exists("./exports"):
            os.mkdir("./exports")
        lay_1 = fig_1['layout']
        title_1 = f'Seismic amplitude, CSIC, {location}, {geo_sel}, channel X, from {start_time} until {end_time}'
        lay_1['title'] = {'font': {'size': 13}, 'text': title_1, 'x': 0.5, 'yanchor': 'top'}
        figx = go.Figure(data=fig_1['data'], layout=lay_1)
        figx.write_image(file="./exports/figx.svg", format="svg", width=1920, height=1080, scale=1)
        lay_2 = fig_2['layout']
        title_2 = f'Seismic amplitude, CSIC, {location}, {geo_sel}, channel Y, from {start_time} until {end_time}'
        lay_2['title'] = {'font': {'size': 13}, 'text': title_2, 'x': 0.5, 'yanchor': 'top'}
        figy = go.Figure(data=fig_2['data'], layout=lay_2)
        figy.write_image(file="./exports/figy.svg", format="svg", width=1920, height=1080, scale=1)
        lay_3 = fig_3['layout']
        title_3 = f'Seismic amplitude, CSIC, {location}, {geo_sel}, channel Z, from {start_time} until {end_time}'
        lay_3['title'] = {'font': {'size': 13}, 'text': title_3, 'x': 0.5, 'yanchor': 'top'}
        figz = go.Figure(data=fig_3['data'], layout=lay_3)
        figz.write_image(file="./exports/figz.svg", format="svg", width=1920, height=1080, scale=1)
        print('Export completed.')

    elif ctx.triggered_id == 'kill_button':
        print('Closing app...')
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

    elif ctx.triggered_id == 'save_config':
        print('Saving configuration...')
        parameters = {'option': OPTION,
                      'start_time': start_time.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                      'end_time': end_time.strftime("%Y-%m-%dT%H:%M:%S.%f"),
                      'geophone': GEOPHONE,
                      'filt_50Hz': filt_50Hz,
                      'format_in': format_in,
                      'location': location,
                      'min_y_fig1': str(min_x),
                      'max_y_fig1': str(max_x),
                      'auto_y_fig1': auto_x,
                      'min_y_fig2': str(min_y),
                      'max_y_fig2': str(max_y),
                      'auto_y_fig2': auto_y,
                      'min_y_fig3': str(min_z),
                      'max_y_fig3': str(max_z),
                      'auto_y_fig3': auto_z}
        create_config(parameters, config_name)

    elif ctx.triggered_id == 'update' and (geo_sel != GEOPHONE or start_time != UTCDateTime(fig_1['data'][0]['x'][0]) or end_time != UTCDateTime(fig_1['data'][0]['x'][-1])):
        GEOPHONE = geo_sel
        [fig_1, fig_2, fig_3, start_time, end_time] = get_3_channel_figures(start_time, end_time, geo_sel,
                                                  filter_50Hz_f, path_root, oversampling_factor, format_in)

    if ctx.triggered_id in ['x_plot', 'y_plot', 'z_plot']:
        if "xaxis.range[0]" in relayoutdata_1:
            start_time = UTCDateTime(relayoutdata_1['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_1['xaxis.range[1]'])
            fig_2['layout']['xaxis']['autorange'] = False
            fig_2['layout']['xaxis']['range'] = [start_time, end_time]
            fig_3['layout']['xaxis']['autorange'] = False
            fig_3['layout']['xaxis']['range'] = [start_time, end_time]

        elif "xaxis.range[0]" in relayoutdata_2:
            start_time = UTCDateTime(relayoutdata_2['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_2['xaxis.range[1]'])
            fig_1['layout']['xaxis']['autorange'] = False
            fig_1['layout']['xaxis']['range'] = [start_time, end_time]
            fig_3['layout']['xaxis']['autorange'] = False
            fig_3['layout']['xaxis']['range'] = [start_time, end_time]

        elif "xaxis.range[0]" in relayoutdata_3:
            start_time = UTCDateTime(relayoutdata_3['xaxis.range[0]'])
            end_time = UTCDateTime(relayoutdata_3['xaxis.range[1]'])
            fig_1['layout']['xaxis']['autorange'] = False
            fig_1['layout']['xaxis']['range'] = [start_time, end_time]
            fig_2['layout']['xaxis']['autorange'] = False
            fig_2['layout']['xaxis']['range'] = [start_time, end_time]

        else:
            start_time = UTCDateTime(fig_1['data'][0]['x'][0])
            end_time = UTCDateTime(fig_1['data'][0]['x'][-1])
            fig_1['layout']['xaxis']['autorange'] = True
            fig_2['layout']['xaxis']['autorange'] = True
            fig_3['layout']['xaxis']['autorange'] = True

    if ctx.triggered_id not in ['export']:
        layout1 = update_layout_3_channels(fig_1, start_time, end_time, min_x, max_x, auto_x)
        fig_1['layout'] = layout1
        layout2 = update_layout_3_channels(fig_2, start_time, end_time, min_y, max_y, auto_y)
        fig_2['layout'] = layout2
        layout3 = update_layout_3_channels(fig_3, start_time, end_time, min_z, max_z, auto_z)
        fig_3['layout'] = layout3

    if type(start_time) is str:  # First time is UTC, after is string
        start_time = UTCDateTime(start_time)
        end_time = UTCDateTime(end_time)
    if ctx.triggered_id is None:
        start_time = UTCDateTime(fig_1['data'][0]['x'][0])
        end_time = UTCDateTime(fig_1['data'][0]['x'][-1])

    print(f'Updating took {round(time.time() - ini_exec_time, 2)} seconds...')
    print('UPDATE COMPLETED!')

    return (fig_1, fig_2, fig_3, {'autosize': True}, {'autosize': True}, {'autosize': True},
            start_time.strftime("%Y-%m-%d %H:%M:%S.%f"), end_time.strftime("%Y-%m-%d %H:%M:%S.%f"))


# Run the app
Timer(1, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)
