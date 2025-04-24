from dash import html
import dash_bootstrap_components as dbc

def not_found_layout():
    return dbc.Container(
        className="d-flex align-items-center justify-content-center vh-100",
        style={"textAlign": "center"},
        children=[
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.H1("404 - Page Not Found", className="text-danger"),
                            html.P(
                                "Sorry, the page does not exist or has been moved.",
                                className="text-muted",
                            ),
                            dbc.Button("Back to Home", href="/home", color="primary", className="mt-3")
                        ]),
                        className="shadow-lg p-4",
                        style={"borderRadius": "15px"}
                    ),
                    width=12
                )
            )
        ]
    )
