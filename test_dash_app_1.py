import os
import signal
from dash import Dash, dcc, html, Input, Output, callback
import webbrowser
from threading import Timer
app = Dash(name=__name__, title='Prueba_1')
app.layout = html.Div([
    html.H6("Change the value in the text box to see callbacks in action!"),
    html.Div([
        "Input: ",
        dcc.Input(id='my-input', value='initial value', type='text')
    ]),
    html.Br(),
    html.Div(id='my-output'),

])


port = 5000 # or simply open on the default `8050` port


def open_browser():
    webbrowser.open_new("http://localhost:{}".format(port))


@callback(
    Output(component_id='my-output', component_property='children'),
    Input(component_id='my-input', component_property='value')
)
def update_output_div(input_value):
    if input_value == 'kill':
        pid = os.getpid()
        print(pid)
        os.kill(pid, signal.SIGTERM)
    return f'Output: {input_value}'


Timer(1, open_browser).start()
app.run(debug=False, port=port)
