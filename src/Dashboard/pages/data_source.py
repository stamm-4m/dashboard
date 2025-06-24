from dash import html,dcc, dash_table
import dash_bootstrap_components as dbc
from Dashboard.InfluxDb import influxdb_handler
from Dashboard.utils.utils_global import disabled_figure

def data_source_layout():
        
        example_data = [
            {"Type": "Sensor", "Name": "Temperature", "Unit": "°C", "Mean": "30", "Max": "40", "Min": "20"},
            {"Type": "Actuator", "Name": "substrate_concentration", "Unit": "g/L", "Mean": "15", "Max": "25", "Min": "10"},
            {"Type": "Computed variable", "Name": "vessel_volume", "Unit": "L", "Mean": "1000", "Max": "1200", "Min": "800"},
        ]

        experiment_columns = [
            {"name": "Experiment ID", "id": "Experiment ID"},
            {"name": "Date", "id": "Date"},
            {"name": "Batch size", "id": "Batch size"},
            {"name": "Temperature", "id": "Temperature"},
            {"name": "Yields", "id": "Yields"},
        ]

        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Data source", className="fw-bold d-inline")
                    ], className="d-flex align-items-left"),
                    dbc.Label("Please choose an Experiment ID to load the available models:", className="fw-bold"),
                    dbc.Label("Experiment ID:", className="fw-bold"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        placeholder="Select Experiment ID",
                        className="mb-3",
                        options=[],
                        persistence=True,
                        persistence_type="local"
                    ),
                    # Row for model details
                    dbc.Label("Project description:", className="fw-bold"),
                    dbc.Row(
                        
                        html.Div(id='project-details')
                        
                    ),
                    # Tabla Experimentos Online
                    html.H5("Experiments online (mean values)", className="text-center mt-4"),
                    html.Div([
                        dash_table.DataTable(
                            id="table-experiments-online",
                            columns=experiment_columns,
                            data=[],
                            page_size=5,
                            style_table={"overflowX": "auto"},
                        )
                    ], className="mb-4"),

                    # Tabla Experimentos Previos
                    html.H5("Previous experiments (mean values)", className="text-center mt-4"),
                    html.Div([
                        dash_table.DataTable(
                            id="table-experiments-previous",
                            columns=experiment_columns,
                            data=[],
                            page_size=5,
                            style_table={"overflowX": "auto"},
                        )
                    ], className="mb-4"),

                ], width=5, className="p-3 bg-light rounded-3 shadow-sm"),
                
                dbc.Col([
                    dcc.Graph(id="bar-chart", figure=disabled_figure),
                    dcc.Graph(id='histogram_experiments', figure=disabled_figure),
                    dcc.Store(id='prev_experiment_ids', data={}),
                    dcc.Interval(
                        id='interval-component',
                        interval=5 * 1000,  # 5 segundos
                        n_intervals=0
                    )
                ], width=7, className="shadow-sm")
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