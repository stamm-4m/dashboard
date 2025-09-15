from dash import html, dcc,dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from Dashboard.utils import model_information
from Dashboard.utils.utils_global import disabled_figure
from Dashboard.utils.utils_performance_estimator import get_performance_estimators_options


def performance_estimator_layout():
        model_name_options = model_information.get_model_name_options()
        metrics_score_options = get_performance_estimators_options()
        # Initialize the figure with a default layout
        return html.Div([
                html.H3("Model divergence", className="text-center"),

                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            # Display experiment-id and model-selected-display
                            dbc.Col([
                                html.Div([
                                    html.Label("Selected model:"),
                                    html.Br(),
                                    html.Label(id="model-selected-display"),
                                ]
                                ),
                                html.Br(),
                                html.Div([
                                    html.Label("Selected experiment:"),                                        
                                    html.Br(),
                                    html.Label(id="experiment-id-display")
                                ])
                            ]),   

                            dbc.Col([
                                html.Label("Monitoring soft sensor:"),
                                dcc.Loading(
                                        id="loading-models",
                                        type="circle",
                                        color="#0d6efd",  # Azul Bootstrap
                                        fullscreen=False,
                                        children=dcc.Dropdown(
                                    id='soft-sensor-input-estimator',
                                    options=model_name_options,
                                    className='mb-2',
                                    placeholder="Select soft sensors",
                                    style={'width': '100%', 'whiteSpace': 'normal'}
                                )),
                                html.Label("Performance estimator:"),
                                dcc.Dropdown(
                                    id='performance-estimator-dropdown',
                                    options=metrics_score_options,
                                    className='mb-2',
                                    searchable=True,
                                    placeholder="Select performance estimator",
                                    style={'width': '100%'}
                                ),
                            ], width=6),                      

                        ])
                    ])
                ], className="mb-3 shadow-sm"),

                html.Div(id="performance-estimator-container"),  # Container where selected metrics will be added

                # Metric result display
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            dbc.Button("Add", id="add-performance-button", color="warning", n_clicks=0, className="px-4"),
                            className="d-flex align-items-center justify-content-center"
                        ),
                       
                    ], width=1, className="d-flex align-items-center"),

                    dbc.Col([
                        html.Div(
                            dbc.Button("Reset", id="reset-performance-button", color="success", n_clicks=0, className="px-4"),
                            className="d-flex align-items-center justify-content-center"
                        ),
                       
                    ], width=1, className="d-flex align-items-center"),

                     
                    dbc.Col([
                        html.Div(id="metrics-result"),
                    ], width=8),
                ], className="mb-4"),

                # Performance section
                html.H4("Select performance estimator", className="text-center mb-3"),

                dbc.Row([
                    # Line chart
                    dbc.Col([
                        dcc.Graph(id="performance-plot", figure=disabled_figure, style={'width': '100%', 'height': '100%'})
                    ], width=12)
                ]),

                html.Br(),
                dbc.Row([
                        dbc.Col([
                                dbc.Accordion(
                                [
                                    dbc.AccordionItem(
                                        [
                                            html.H5("Detailed Prediction and Metrics Table", className="mb-3"),
                                            html.Div(id='metrics-div'),
                                            dash_table.DataTable(
                                                id='metrics-table',
                                                style_table={'overflowX': 'auto'},
                                                style_cell={'textAlign': 'center', 'padding': '5px'},
                                                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                                                page_size=40,
                                                )
                                        ],
                                        title="Show Detailed Metrics"
                                    ),
                                ],
                                start_collapsed=False  # Accordion starts closed
                            )
                        ], width=12),
                ], className="mb-4"),

            ], className="container")
