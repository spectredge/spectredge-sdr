import os
from flask import Flask, render_template, make_response
from blade import draw_graph, setup_device
import atexit

app = Flask(
    __name__,
   template_folder=os.path.abspath('web/templates/'),
   static_folder=os.path.abspath('web/static')
)

device=setup_device()

def close_device():
    if device is not None:
        device.close()

atexit.register(close_device)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/refresh_graph")
def refresh_graph():
    try:
        print('Refreshing graph.')
        draw_graph(device=device)
        return make_response('OK', 200)
    except Exception as ex:
        print(ex)
        return make_response(str(ex), 500)

