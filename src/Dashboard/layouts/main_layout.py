from dash import html, dcc
import dash_bootstrap_components as dbc
from Dashboard.components.sidebar import sidebar

def layout(session_data=None):
    return dbc.Container([
        # Location component to monitor the URL
        #dcc.Location(id="url", refresh=False),  # Captures changes in the URL
        dbc.Row([
            dbc.Col(sidebar(session_data),className="sidebar"),
            dbc.Col(html.Div(id="main-content", className="content"))
        ])
    ], fluid=True)
