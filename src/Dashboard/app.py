from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import Dashboard.callbacks  # Load all callbacks
import logging
import sys

import flask
import os

# Cambiar el logger raíz
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Evitar múltiples handlers si se recarga
if not root_logger.hasHandlers():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)s:%(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

# Create the Flask server
server = flask.Flask(__name__)

# Create the Dash application and connect it with Flask
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], server=server, suppress_callback_exceptions=True)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),        # Detecta cambios de ruta (como /logout)
    dcc.Store(id="user-session", storage_type="session"),  # Guarda info del usuario logueado
    html.Div(id="page-content")                   # Aquí se carga login o dashboard
])

def main():
    app.run(debug=True, host="0.0.0.0", port=8050)

if __name__ == "__main__":
    main()
