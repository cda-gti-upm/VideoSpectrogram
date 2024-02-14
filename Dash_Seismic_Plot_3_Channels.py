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
from seismic_dash_utils import (open_browser, get_3_channel_figures, update_layout_3_channels)
import plotly.graph_objs as go



args = sys.argv
geophone = args[1]
start = args[2]
end = args[3]
filt_50Hz = args[4]
format_in = args[5]
location = args[6]

oversampling_factor = 40
sock = socket.socket()
sock.bind(('', 0))
port = sock.getsockname()[1]
del sock

styles = {'pre': {'border': 'thin lightgrey solid', 'overflowX': 'scroll'}}
path_root = f'./data/CSIC_{location}'

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


[fig1, fig2, fig3, starttime, endtime] = get_3_channel_figures(starttime, endtime, geophone, filter_50Hz_f, path_root, oversampling_factor, format_in)


# Creating app layout:

app = Dash(__name__)
app.layout = html.Div([
    dcc.Dropdown(['Geophone1', 'Geophone2', 'Geophone3', 'Geophone4',
                  'Geophone5', 'Geophone6', 'Geophone7', 'Geophone8'], id='geophone_selector', value=geophone),
    html.Div(
        ['Select the start and end time (format: yyyy-mm-dd hh:mm:ss): ',
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
             style={'display': 'inline-block'},),
         '  ',
         html.Button('Read new data', id='update', n_clicks=0),
         '  ',
         html.Button('Export in SVG', id='export', n_clicks=0),
         '   ',
         html.Button('Close app', id='kill_button', n_clicks=0)],
    ),
    html.Div(children=[
        html.Div(
            children=[dcc.Checklist(id='auto_x', options=['autorange'], value=['autorange']),
                      html.Div('Channel X amplitude range (min to max)'),
                      dcc.Input(
                          id='min_x',
                          type='number',
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_x',
                          type='number',
                          value=0,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_y', options=['autorange'], value=['autorange']),
                      html.Div('Channel Y amplitude range (min to max)'),
                      dcc.Input(
                          id='min_y',
                          type='number',
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_y',
                          type='number',
                          value=0,
                          debounce=True
                      )],
            style={'display': 'in-line-block', 'padding-right': '0.5em'}),
        html.Div(
            children=[dcc.Checklist(id='auto_z', options=['autorange'], value=['autorange']),
                      html.Div('Channel Z amplitude range (min to max)'),
                      dcc.Input(
                          id='min_z',
                          type='number',
                          value=0,
                          debounce=True
                      ),
                      dcc.Input(
                          id='max_z',
                          type='number',
                          value=0,
                          debounce=True
                      )],
            style={'display': 'in-line-block'})],
        style={'display': 'flex'}),
    dcc.Graph(id='x_plot', figure=fig1, style={'width': '170vh', 'height': '25vh'}, relayoutData={'autosize': True}),
    dcc.Graph(id='y_plot', figure=fig2, style={'width': '170vh', 'height': '25vh'}, relayoutData={'autosize': True}),
    dcc.Graph(id='z_plot', figure=fig3, style={'width': '170vh', 'height': '25vh'}, relayoutData={'autosize': True})
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
    State('startdate', 'value'),
    State('enddate', 'value'),
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
    State('geophone_selector', 'value'),
    Input('update', 'n_clicks'),
    Input('export', 'n_clicks'),
    State('x_plot', 'figure'),
    State('y_plot', 'figure'),
    State('z_plot', 'figure'),
)
def update_plot(starttime_app, endtime_app, relayoutdata_1, relayoutdata_2, relayoutdata_3, max_x, min_x, max_y,
                min_y, max_z, min_z, auto_x, auto_y, auto_z, button, geo_sel, update, export_button, fig_1, fig_2, fig_3):

    start_time = UTCDateTime(starttime_app)
    end_time = UTCDateTime(endtime_app)
    if ctx.triggered_id == 'export':
        if not os.path.exists("./exports"):
            os.mkdir("./exports")

        lay_1 = fig_1['layout']
        title_1 = f'Seismic amplitude, CSIC, {location}, {geo_sel}, channel X, from {start_time} until {endtime}'
        lay_1['title'] = {'font': {'size': 13}, 'text': title_1, 'x': 0.5, 'yanchor': 'top'}
        figx = go.Figure(data=fig_1['data'], layout=lay_1)
        figx.write_image(file="./exports/figx.svg", format="svg", width=1920, height=1080, scale=1)

        lay_2 = fig_2['layout']
        title_2 = f'Seismic amplitude, CSIC, {location}, {geo_sel}, channel Y, from {start_time} until {endtime}'
        lay_2['title'] = {'font': {'size': 13}, 'text': title_2, 'x': 0.5, 'yanchor': 'top'}
        figy = go.Figure(data=fig_2['data'], layout=lay_2)
        figy.write_image(file="./exports/figy.svg", format="svg", width=1920, height=1080, scale=1)

        lay_3 = fig_3['layout']
        title_3 = f'Seismic amplitude, CSIC, {location}, {geo_sel}, channel Z, from {start_time} until {endtime}'
        lay_3['title'] = {'font': {'size': 13}, 'text': title_3, 'x': 0.5, 'yanchor': 'top'}
        figz = go.Figure(data=fig_3['data'], layout=lay_3)
        figz.write_image(file="./exports/figz.svg", format="svg", width=1920, height=1080, scale=1)
        print('Export completed.')


    if ctx.triggered_id == 'kill_button':
        pyautogui.hotkey('ctrl', 'w')
        pid = os.getpid()
        os.kill(pid, signal.SIGTERM)

    if ctx.triggered_id == 'update':
        [fig_1, fig_2, fig_3, start_time, end_time] = get_3_channel_figures(start_time, end_time, geo_sel,
                                                                            filter_50Hz_f, path_root,
                                                                            oversampling_factor, format_in)


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

        if ctx.triggered_id != 'export':
            layout1 = update_layout_3_channels(fig_1, start_time, end_time, min_x, max_x, auto_x)
            fig_1['layout'] = layout1
            layout2 = update_layout_3_channels(fig_2, start_time, end_time, min_y, max_y, auto_y)
            fig_2['layout'] = layout2
            layout3 = update_layout_3_channels(fig_3, start_time, end_time, min_z, max_z, auto_z)
            fig_3['layout'] = layout3

    return (fig_1, fig_2, fig_3, {'autosize': True}, {'autosize': True}, {'autosize': True},
            start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S"))


 # Run the app
Timer(5, open_browser, args=(port,)).start()
app.run_server(debug=False, port=port)
