from dash import html, dcc
import dash_bootstrap_components as dbc


from ..InfluxDb import influxdb_handler
from ..utils import model_selector


def data_drift_layout():
        experiments_id = influxdb_handler.get_experiment_ids_from_bucket()
        model_name_options = model_selector.get_model_name_options()
        metrics_score_options = model_selector.get_metrics_score_options()
    
        return html.Div([
            html.H3("Data drift detectors", className="text-center"),
            
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
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
                        ], width=5),

                        dbc.Col([
                            html.Label("Input model:"),
                            dcc.Dropdown(
                                id='input-model-dropdown',
                                options=[],
                                className='mb-2',
                                searchable=True,
                                placeholder="Select Input Model",
                                style={'width': '100%'}
                            ),
                        ], width=3),

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
                        ], width=2),

                        dbc.Col([
                            html.Label("Metric score:"),
                            dcc.Dropdown(
                                id='metric-score-dropdown',
                                options=metrics_score_options,
                                className='mb-2',
                                searchable=True,
                                placeholder="Select Metric Score",
                                style={'width': '100%'}
                            ),
                        ], width=2)
                    ])
                ])
            ], className="mb-3 shadow-sm"),
            html.Div(id="metrics-container"),  # Contenedor donde se agregarán las métricas seleccionadas
            # Metric result display
            dbc.Row([
                dbc.Col([
                    html.Div(
                    html.Button("Run", id="add-metric-button", className="btn btn-warning", n_clicks=0),
                    className="d-flex align-items-center justify-content-center"
                    ),
                    ], width=1, className="d-flex align-items-center"),
                dbc.Col([
                    html.Div(id="metrics-result"),
                ], width=3),
            ], className="mb-4"),

            # Monitored inputs section
            html.H4("Monitored inputs", className="text-center mb-3"),

            dbc.Row([
                #  Graph linea
                dbc.Col([
                    # Componente gráfico vacío inicial
                    dcc.Graph(id="density-plot", figure={})

                ], width=6),

                #  Graph histogram
                dbc.Col([
                   
                    dcc.Graph(id='density-plot-hist',figure={}),
                    
                ], width=6),
            ])
        ], className="container")

    
         
