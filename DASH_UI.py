from dash import Dash, dcc, html, Input, Output, callback
import dash_daq as daq
import os
import subprocess
import signal

devnull = open(os.devnull, 'wb')
proc = subprocess.Popen(['python', 'test_dash_app_1.py'], stdout=devnull, stderr=devnull)
print(f'El proceso hijo tiene de PID {proc.pid}')
print(f'El proceso padre tiene de PID {os.getpid()}')
app = Dash(name=__name__, title='Seismic UI')
app.layout = html.Div([
    daq.PowerButton(
        id='our-power-button-1',
        on=True
    ),
    html.Div(id='power-button-result-1')
])


@callback(
    Output('power-button-result-1', 'children'),
    Input('our-power-button-1', 'on'),
    prevent_initial_callback=True
)
def update_output(on):
    print(os.getpid())
    if not on:
        proc.kill()
        os.kill(os.getpid(), signal.SIGTERM)
    return f'The button is {on}.'


if __name__ == '__main__':
    app.run(debug=False)
