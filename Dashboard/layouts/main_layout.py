from dash import html, dcc
import dash_bootstrap_components as dbc
from components.sidebar import sidebar

def layout():
    return dbc.Container([
        # Location component to monitor the URL
        dcc.Location(id="url", refresh=False),  # Captures changes in the URL
        dbc.Row([
            dbc.Col(sidebar(),className="sidebar"),
            dbc.Col(html.Div(id="page-content", className="content"))
        ])
    ], fluid=True)