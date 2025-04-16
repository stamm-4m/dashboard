from dash import html, dcc
import dash_bootstrap_components as dbc
from ..components.sidebar import sidebar
import logging

def layout():
    logging.debug("Creating main layout")
    return dbc.Container([
        # Componente de ubicación para monitorear la URL
        dcc.Location(id="url", refresh=False),  # Captura cambios en la URL
        dbc.Row([
            dbc.Col(sidebar(),className="sidebar"),
            dbc.Col(html.Div(id="page-content", className="content"))
        ])
    ], fluid=True)