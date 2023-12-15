from flask import Flask
from dash import Dash, html, Input, ctx, Output
from wsgiref.simple_server import make_server
import threading
import time


global keepPlot
keepPlot = True
def stop_execution():
    global keepPlot
    # stream.stop_stream()
    keepPlot = False
    print(keepPlot)
    # stop the Flask server
    server.shutdown()
    server_thread.join()
    print("Dash app stopped gracefully.")


server = Flask(__name__)
app = Dash(__name__, server=server)
app.layout = html.Div([
    html.Button('Submit', id='submit-val'),
    html.Div('hola', id='text')
])


def start_dash_app():
    app.run_server(debug=False, use_reloader=False)


@app.callback(Output('text', 'value'),
              Input('submit-val', 'n-clicks'),
              prevent_initial_callback=True
              )
def update(boton):
    print(ctx.triggered_id)
    if ctx.triggered_id == 'submit-val':
        stop_execution()
    return "adios"


# create a server instance
server = make_server("localhost", 8051, server)
# start the server in a separate thread
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()


# start the Dash app in a separate thread

dash_thread = threading.Thread(target=start_dash_app)
dash_thread.start()

while keepPlot:
    time.sleep(1)  # keep the main thread alive while the other threads are running

