from dash import Dash, html
import dash_bootstrap_components as dbc
from Dashboard.layouts.main_layout import layout
import Dashboard.callbacks  # Load all callbacks
from Dashboard.InfluxDb import InfluxDBHandler

import flask
import os

def main():
    # Create the Flask server
    server = flask.Flask(__name__)

    # Create the Dash application and connect it with Flask
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, suppress_callback_exceptions=True)

    app.layout = layout()

    app.run(debug=True, host="0.0.0.0", port=8050)

if __name__ == "__main__":
    main()
