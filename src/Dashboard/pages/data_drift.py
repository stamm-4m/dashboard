from dash import html, dcc
import dash_bootstrap_components as dbc

from Dashboard.InfluxDb import influxdb_handler
from Dashboard.utils import model_information
from Dashboard.utils.utils_data_drift import get_metrics_score_options

def data_drift_layout():
        experiments_id = influxdb_handler.get_experiment_ids_from_bucket()
        model_name_options = model_information.get_model_name_options()
        metrics_score_options = get_metrics_score_options()
    
        return html.Div([
            html.H3("Data drift detectors", className="text-center"),
            
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Monitoring soft sensor:"),
                            dcc.Loading(
                                id="loading-models-soft",
                                type="circle",
                                color="#0d6efd",  # Azul Bootstrap
                                fullscreen=False,
                                children=dcc.Dropdown(
                                        id='soft-sensor-input',
                                        options=model_name_options,
                                        className='mb-2',
                                        searchable=True,
                                        placeholder="Select soft sensors",
                                        style={'width': '100%', 'whiteSpace': 'normal'}
                                    )
                                ),
                        ], width=6),

                        dbc.Col([
                            html.Label("Drift detector:"),
                            dcc.Dropdown(
                                id='metric-score-dropdown',
                                options=metrics_score_options,
                                className='mb-2',
                                searchable=True,
                                placeholder="Select Metric Score",
                                style={'width': '100%'}
                            ),
                        ], width=6)
                        
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Experiment ID:"),
                            dcc.Dropdown(
                                id='input-experiment-dropdown',
                                    options=experiments_id,
                                    className='mb-2',
                                    searchable=True,
                                    placeholder="Select experiment ID",
                                    style={'width': '100%'}
                                ),
                        ], width=6),
                        dbc.Col([
                            # Time range
                            dbc.Label("Time range selection:"),
                            dcc.RangeSlider(
                                id="time-window-size-drift",
                                min=0,
                                max=0,
                                step=1,
                                marks=None,
                                value=[0, 100],
                                tooltip={
                                        "placement": "bottom",
                                        "always_visible": True,
                                        "style": {"color": "LightSteelBlue", "fontSize": "20px"},
                                }
                                ),
                            html.Div(id="time-ws-slider-labels-drift", style={"textAlign": "center", "marginBottom": "20px"}),
                        ],width=6)
                    ])
                ])
            ], className="mb-3 shadow-sm"),
            html.Div(id="metrics-container"),  # Container where selected metrics will be added
            
            # Metric result display
            dbc.Row([
                dbc.Col([
                    html.Div(
                    html.Button("Run", id="add-metric-button", className="btn btn-warning", n_clicks=0),
                    className="d-flex align-items-center justify-content-center"
                    ),
                    ], width=4, className="d-flex align-items-center"),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([    
                    html.Div(
                        id="metrics-result",
                        className="d-flex align-items-center justify-content-center")
                        ], width=4, className="d-flex align-items-center"),
            ]),
            dbc.Row([
            dbc.Col([
                html.Div(id='graph-details', style={"display": "none"}, children=[
                    dbc.Accordion([
                        dbc.AccordionItem(
                            title=html.Div("Monitored inputs"),
                            children=[
                                dbc.Row([
                                    dbc.Col([
                                        dcc.Graph(id="density-plot", figure={})
                                    ], width=12)#,
                                    #dbc.Col([
                                    #    dcc.Graph(id='density-plot-hist', figure={})
                                    #], width=6),
                                ], className="mb-4")
                            ],
                         
                        )
                    ], start_collapsed=True, flush=False)
                ])
            ], width=12)
        ])
    ], className="container")