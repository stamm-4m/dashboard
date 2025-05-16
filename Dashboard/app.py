from dash import Dash, html
import dash_bootstrap_components as dbc
from layouts.main_layout import layout
import callbacks  # Load all callbacks
from InfluxDb import InfluxDBHandler
import logging
import sys

import flask
import os

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Create the Flask server
server = flask.Flask(__name__)

# Create the Dash application and connect it with Flask
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, suppress_callback_exceptions=True)

app.layout = layout()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
