from dash import html
import dash_bootstrap_components as dbc

def home_layout():
    return dbc.Container(
        fluid=True,
        className="d-flex flex-column align-items-center justify-content-center vh-100",
        children=[
            dbc.Card(
                dbc.CardBody([
                    html.H1("Welcome to the STAMM", className="text-primary text-center"),
                    html.P(
                        "This application guides you through a structured workflow for managing and monitoring MLOps pipelines.",
                        className="text-center"
                    ),
                    html.Hr(),
                    html.H4("How to Use the Sidebar:", className="text-secondary"),
                    html.Ul([
                        html.Li("Start by selecting '1. Data Source' to load and configure your data."),
                        html.Li("Once a dataset is selected, '2. Soft Sensors' will be enabled."),
                        html.Li("After setting up soft sensors, '3. Monitoring' will be unlocked."),
                        html.Li("Finally, '4. Maintenance' is enabled for system updates and logs."),
                    ]),
                    html.P("Each step must be completed before the next becomes available.", className="text-danger"),
                    dbc.Button("Go to Data Source", href="/data-source", color="primary", className="mt-3"),
                ]),
                className="shadow-lg p-4",
                style={"maxWidth": "600px", "borderRadius": "15px"}
            )
        ]
    )
