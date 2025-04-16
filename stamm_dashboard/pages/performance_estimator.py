from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from ..utils import model_selector


def performance_estimator_layout():
        model_name_options = model_selector.get_model_name_options()
        metrics_score_options = model_selector.get_performance_estimators_options()
        # Inicializa la figura con un layout predeterminado
        global disabled_figure 
        disabled_figure = {
            "data": [],
            "layout": go.Layout(
                xaxis={"title": "X Axis", "visible": False},
                yaxis={"title": "Y Axis", "visible": False},
                annotations=[
                    {
                        "text": "Graph Disabled",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": "gray"},
                    }
                ],
                plot_bgcolor="lightgray",  # Fondo gris para efecto "deshabilitado"
                paper_bgcolor="lightgray",
            ),
        }

        return html.Div([
                html.H3("Performance estimator", className="text-center"),

                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            # Display experiment-id y model-selected-display
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
                                dcc.Dropdown(
                                    id='soft-sensor-input',
                                    options=model_name_options,
                                    className='mb-2',
                                    searchable=True,
                                    placeholder="Select soft sensors",
                                    style={'width': '100%', 'whiteSpace': 'normal'}
                                ),
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

                html.Div(id="performance-estimator-container"),  # Contenedor donde se agregarán las métricas seleccionadas

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
                    # Gráfico de línea
                    dbc.Col([
                        dcc.Graph(id="performance-plot", figure=disabled_figure, style={'width': '100%', 'height': '100%'})
                    ], width=12)
                ])
            ], className="container")

    
        

