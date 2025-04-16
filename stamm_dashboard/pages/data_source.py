from dash import html,dcc, dash_table
import dash_bootstrap_components as dbc
from ..InfluxDb import influxdb_handler
from ..utils.utils_global import disabled_figure

def data_source_layout():
        buckets_options = [{"label": b, "value": b} for b in influxdb_handler.get_buckets()]

        example_data = [
            {"Type": "Sensor", "Name": "Temperature", "Unit": "°C", "Mean": "30", "Max": "40", "Min": "20"},
            {"Type": "Actuator", "Name": "substrate_concentration", "Unit": "g/L", "Mean": "15", "Max": "25", "Min": "10"},
            {"Type": "Computed variable", "Name": "vessel_volume", "Unit": "L", "Mean": "1000", "Max": "1200", "Min": "800"},
        ]

        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H2("Data:", className="fw-bold d-inline"),
                        dbc.RadioItems(
                            id="real-time-radio",
                            options=[{"label": "ONLINE", "value": "ON"}, {"label": "OFFLINE", "value": "OFF"}],
                            value="OFF",
                            persistence=True,
                            persistence_type="local",
                            inline=True,
                            className="ms-3"
                        )
                    ], className="d-flex align-items-center mb-3"),

                    dbc.Label("Bucket:", className="fw-bold"),
                    dcc.Dropdown(
                        id="bucket-dropdown",
                        placeholder="Select Bucket",
                        className="mb-3",
                        options=buckets_options,
                        persistence=True,
                        persistence_type="local"
                    ),

                    dbc.Label("Experiment ID:", className="fw-bold"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        placeholder="Select Experiment ID",
                        className="mb-3",
                        options=[],
                        persistence=True,
                        persistence_type="local"
                    ),
                ], width=4, className="p-3 bg-light rounded-3 shadow-sm"),

                dbc.Col([
                    dcc.Graph(id="bar-chart", figure=disabled_figure)
                ], width=8, className="shadow-sm")
            ], className="my-4"),

            dbc.Row([
                html.Div("Duration: N/A", id="duration-text", className="fw-bold text-primary fs-5 mb-3")
            ]),

            dbc.Row([
                dash_table.DataTable(
                    id="data-table",
                    columns=[
                        {"name": "Type", "id": "Type"},
                        {"name": "Name", "id": "Name"},
                        {"name": "Unit", "id": "Unit"},
                        {"name": "Mean", "id": "Mean"},
                        {"name": "Max", "id": "Max"},
                        {"name": "Min", "id": "Min"}
                    ],
                    data=example_data,
                    page_size=10,
                )
            ])
        ], fluid=True)