import dash
from dash import html, dcc, Input, Output,State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np
import scipy.stats as stats

from ..utils import model_selector
from ..InfluxDb import influxdb_handler # recuperamos la instancia creada


#load input for each model selected
@dash.callback(
        Output('input-model-dropdown', 'options'),
        Input('soft-sensor-input', 'value'),
        prevent_initial_call=True
)
def update_input_options(selected_model):
            print("value",selected_model)
            if selected_model:
                return model_selector.load_inputs_from_yaml(selected_model)
            return []  # Si no hay modelo seleccionado, se deja vacío
        # Load metrics selected
@dash.callback(
            Output("metrics-container", "children"),
            Input("metric-score-dropdown", "value")
)
def update_metrics_section(selected_metric):
            if not selected_metric:
                return html.Div()  # Si no hay métrica seleccionada, se retorna un div vacío

            # Obtener información de la métrica seleccionada
            metric_info = model_selector.load_metric_descriptions(selected_metric)
            if not metric_info:
                return html.Div(html.P("No information available for this metric."))

            # Obtener los parámetros de configuración de la métrica
            method_params = metric_info.get("configuration", {}).get("method_parameters", [])
            
            # Construcción dinámica de los inputs
            new_metric_section = dbc.Card([
                                    dbc.CardBody([
                                        dbc.Row([
                                            # Columna izquierda: Inputs alineados
                                            dbc.Col([
                                                html.H6("Metric Parameters", className="mb-3"),
                                                *[
                                                    dbc.Row([
                                                        dbc.Col(
                                                            html.Label([
                                                                f"{param.get('name', 'unknown')}",
                                                                dbc.Tooltip(param.get('description', 'No description available'),
                                                                            target=f"input-{selected_metric}-{param.get('name', 'unknown')}")
                                                            ]), width=6, className="d-flex align-items-center"
                                                        ),
                                                        dbc.Col(
                                                            dcc.Input(
                                                                id=f"input-{selected_metric}-{param.get('name', 'unknown')}",
                                                                type="number",
                                                                value=param.get('default', 0),
                                                                className="mb-2",
                                                                style={'width': '100%'}
                                                            ), width=6
                                                        )
                                                    ], className="mb-2")
                                                    for param in method_params
                                                ]
                                            ], width=6),

                                            # Columna derecha: Descripción y thresholds bien distribuidos
                                            dbc.Col([
                                                html.H6("Metric Description", className="mb-3"),
                                                dbc.ListGroup([
                                                    dbc.ListGroupItem(f"{key}: {value}") for key, value in metric_info.get("thresholds", {}).items()
                                                ])
                                            ], width=6),
                                        ])
                                    ])
                                ], className="mb-3 shadow-sm")
            return new_metric_section
        
        # Callback para generar los graficos de densidad
@dash.callback(
            Output("density-plot", "figure"),
            Output("density-plot-hist", "figure"),
            Output("metrics-result","children"),
            Input("add-metric-button", "n_clicks"),
            State("soft-sensor-input", "value"),
            State("input-experiment-dropdown", "value"),
            State("input-model-dropdown", "value"),
            prevent_initial_call=True
        )
def update_density_plot(n_clicks, soft_sensor, experiment_id, selected_input):
            if not (soft_sensor and experiment_id and selected_input):
                return dash.no_update  # Evita actualizar si faltan valores

            # 1. Obtener datos del YAML del modelo seleccionado
            config = model_selector.get_configuration_by_model_name(soft_sensor)  # Debes implementar esta función
            #print("config",config)
            model_config = config.get('ml_model_configuration', {})
            training_info = model_config["training_information"]
            #print("training_info",training_info)
            # 2. Extraer valores de experiments_id
            experiments_id = training_info.get("experiments_ID", {})
            print("experiments_id",experiments_id)
            if not experiments_id:
                return dash.no_update  # Evita errores si no se encuentran datos

            # 3. Consultar InfluxDB para obtener datos de entrenamiento y prueba
            training_data = influxdb_handler.get_data_training(experiments_id,selected_input)  # Implementar función
            
            test_data = influxdb_handler.get_data_test(experiment_id, selected_input)  # Implementar función
            #create copy to generate data random test
            if len(training_data) == 0:
                if isinstance(test_data, list):
                    test_d = np.array(test_data)
                    noise = np.random.normal(0, 0.1, size=test_d.shape)
                    training_data = test_d + noise
            
            print("training_data",training_data)

            print("test_data",test_data)

            # 4. Crear el gráfico de densidad
            fig = go.Figure()
            #fig3 = go.Figure()

            # KDE para Training Set
            fig.add_trace(go.Histogram(
                x=training_data, histnorm='probability density', name='Training Set',
                opacity=0.5, marker=dict(color='blue')
            ))

            # KDE para Test Set
            fig.add_trace(go.Histogram(
                x=test_data, histnorm='probability density', name='Test Set',
                opacity=0.5, marker=dict(color='red')
            ))

            # Layout de la gráfica
            fig.update_layout(
                title=f" Density of Training and Test Sets Histogram({selected_input})",
                xaxis_title=selected_input,
                yaxis_title="Density",
                barmode="overlay",  # Sobreponer ambas distribuciones
                template="plotly_white"
            )
            # Layout de la gráfica
            #fig3.update_layout(
            #    title=f" Density of Training and Test Sets Histogram({selected_input})",
            #    xaxis_title=selected_input,
            #    yaxis_title="Density",
            #    barmode="overlay",  # Sobreponer ambas distribuciones
            #    template="plotly_white"
            #)
            fig2 = go.Figure()
            #fig4 = go.Figure()
            # Calcular KDE para Training Set
            train_kde = stats.gaussian_kde(training_data)
            train_x = np.linspace(min(training_data), max(training_data), 100)
            train_y = train_kde(train_x)

            # Calcular KDE para Test Set
            test_kde = stats.gaussian_kde(test_data)
            test_x = np.linspace(min(test_data), max(test_data), 100)
            test_y = test_kde(test_x)

            # Agregar KDE para Training Set como área
            fig2.add_trace(go.Scatter(
                x=train_x, y=train_y, mode='lines', name='Training Set',
                fill='tozeroy', line=dict(color='blue', width=2), opacity=0.5
            ))

            # Agregar KDE para Test Set como área
            fig2.add_trace(go.Scatter(
                x=test_x, y=test_y, mode='lines', name='Test Set',
                fill='tozeroy', line=dict(color='red', width=2), opacity=0.5
            ))

            # Layout de la gráfica
            fig2.update_layout(
                title=f"Density of Training and Test Sets ({selected_input})",
                xaxis_title=selected_input,
                yaxis_title="Density",
                template="plotly_white"
            )
            # Layout de la gráfica
            #fig4.update_layout(
            #    title=f"Density of Training and Test Sets ({selected_input})",
            #    xaxis_title=selected_input,
            #    yaxis_title="Density",
            #    template="plotly_white"
            #)

            metric_result = html.Label(f"Metric result: {0.17}")  

            return fig2, fig, metric_result