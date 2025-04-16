import re

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import html, dcc, Input, Output, State, ALL
from dash.exceptions import PreventUpdate

from ..InfluxDb import influxdb_handler
from ..utils import model_selector
from ..utils.utils_performance_estimator import calculate_cossim, calculate_cv, calculate_mae, calculate_mse, \
    calculate_pcc, calculate_rmse, calculate_vpd, get_next_color, generate_prediction_name


@dash.callback(
            Output("performance-plot", "figure", allow_duplicate=True),
            Output("performance-estimator-container", "children",allow_duplicate=True),
            Output("soft-sensor-input", "value"),
            Output("performance-estimator-dropdown", "value"),  
            Input("reset-performance-button", "n_clicks"),
            prevent_initial_call=True
)
def reset_performance_plot(n_clicks):
            global disabled_figure
            fig = go.Figure(disabled_figure)
            return disabled_figure, html.Div(), "","" 

           

@dash.callback(
            Output("model-selected-display", "children"),
            Input("model-data-store", "data")
)
def update_model_display(data):
            if not data or "model_name" not in data or not data["model_name"]:
                return "No Model Selected"
            return f"{data['model_name']}"
@dash.callback(
            Output("experiment-id-display", "children"),
            Input("store-selected-state", "data"),
)
def update_experiment_display(data):
            if not data or "selected_experiment" not in data or not data["selected_experiment"]:
                return "No experiment ID Selected"
            return f"{data['selected_experiment']}"
        
        #load input for each model selected
@dash.callback(
            Output('input-model-dropdown', 'options',allow_duplicate=True),
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
            Output("performance-estimator-container", "children"),
            Input("performance-estimator-dropdown", "value")
)
def update_estimator_section(selected_metric):
            if not selected_metric:
                return html.Div()  # Si no hay métrica seleccionada, se retorna un div vacío

            # Obtener información de la STIMAROE seleccionada
            metric_info = model_selector.load_estimator_descriptions(selected_metric)
            if not metric_info:
                return html.Div(html.P("No information available for this performance estimator."))

            threshold_colors = {"low": "success", "moderate": "warning", "high": "danger"}

            # Obtener los parámetros de configuración de la métrica
            method_info = metric_info.get("method", {})
            formula = method_info.get("formula", "No formula available")
            thresholds = method_info.get("thresholds", {})
            method_params = metric_info.get("configuration", {}).get("method_parameters", [])
            implementation_notes = metric_info.get("implementation_notes", [])
            new_estimator_section = dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        # Columna izquierda: Fórmula, parámetros y notas de implementación
                        dbc.Col([
                            html.H6("Metric Description", className="mb-3"),
                            html.P(formula, className="mb-3"),
                            html.H6("Parameters", className="mb-2"),
                            *[
                                dbc.Row([
                                    dbc.Col(
                                        html.Label([
                                            f"{param.get('name', 'unknown')}",
                                            dbc.Tooltip(param.get('description', 'No description available'),
                                                        target=f"input-parameter")
                                        ]), width=6, className="d-flex align-items-center"
                                    ),
                                    dbc.Col(
                                        dcc.Input(
                                            id={"type": "dynamic-input", "index": "input-parameter"}, 
                                            type="number",
                                            value=param.get('default', 0),
                                            className="mb-2",
                                            style={'width': '100%'}
                                        ), width=6
                                    )
                                ], className="mb-2")
                                for param in method_params
                            ],
                            html.H6("Implementation Notes", className="mt-3"),
                            html.Ul([html.Li(note) for note in implementation_notes])
                        ], width=6),
                        
                        # Columna derecha: Thresholds con colores
                        dbc.Col([
                            html.H6("Metric Thresholds", className="mb-3"),
                            dbc.ListGroup([
                                dbc.ListGroupItem(f"{key}: {value}", color=threshold_colors.get(key, "light"))
                                for key, value in thresholds.items()
                            ])
                        ], width=6),
                    ])
                ])
            ], className="mb-3 shadow-sm")

            return new_estimator_section
         

@dash.callback(
            Output("performance-plot", "figure"),
            Input("add-performance-button", "n_clicks"),
            State("soft-sensor-input", "value"),  
            Input("store-selected-state", "data"),
            Input("model-data-store", "data"),
            Input("performance-estimator-dropdown", "value"),  
            State({"type": "dynamic-input", "index": ALL}, "value"),  
            State("performance-plot", "figure"),  
            prevent_initial_call=True
)
def update_performance_plot(n_clicks, model_selected, experiment_id,model_data_selected, selected_metric, param_values, figure_data):
            global disabled_figure
    
            # Inicializa la figura por defecto
            fig = go.Figure(disabled_figure)

            ctx = dash.callback_context
            if not ctx.triggered:
                raise PreventUpdate

            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # Función para extraer valores numéricos de los umbrales
            def extract_threshold_value(text):
                numbers = re.findall(r"[-+]?\d*\.?\d+", text)  # Encuentra números en el texto
                return float(numbers[0]) if numbers else None  # Retorna el primer número encontrado

            # **Caso 1: Agregar Umbrales**
            if triggered_id == "performance-estimator-dropdown" and selected_metric:
                fig = go.Figure()
                metric_info = model_selector.load_estimator_descriptions(selected_metric)
                if metric_info:
                    # Definir colores según el nivel del umbral
                    threshold_colors = {"low": "green", "moderate": "orange", "high": "red"}
                    thresholds = metric_info.get("method", {}).get("thresholds", {})
                    # Extraer valores de umbrales
                    low_threshold = extract_threshold_value(thresholds.get("low", ""))
                    moderate_threshold = extract_threshold_value(thresholds.get("moderate", ""))
                    high_threshold = extract_threshold_value(thresholds.get("high", ""))
                    # Ajustar los límites del eje Y para un rango más amplio
                    fig.update_layout(
                        yaxis_range=[0, (high_threshold+2)],  # Asegurar que el eje X comience en 0
                        margin=dict(l=0, r=70, t=10, b=10),  # Márgenes mínimos
                        
                    )
                    # Agregar áreas coloreadas
                    if high_threshold is not None:
                        fig.add_hrect(y0=high_threshold, y1=10,  # Desde el umbral alto hasta el infinito
                                    fillcolor="red", opacity=0.2, layer="below", line_width=0)
                    
                    if low_threshold is not None:
                        fig.add_hrect(y0=-1, y1=low_threshold,  # Desde 0 hasta el umbral bajo
                                    fillcolor="green", opacity=0.2, layer="below", line_width=0)

                    # Agregar área intermedia (moderate) en naranja
                    if low_threshold is not None and high_threshold is not None:
                        fig.add_hrect(y0=low_threshold, y1=high_threshold,  # Entre los dos umbrales
                                    fillcolor="orange", opacity=0.2, layer="below", line_width=0)
                    # Agregar líneas horizontales para los umbrales
                    for key, value in thresholds.items():
                        if key != "moderate":
                            threshold_value = extract_threshold_value(value)
                            if threshold_value is not None:
                                fig.add_hline(
                                    y=threshold_value,
                                    line=dict(color=threshold_colors.get(key, "black"), width=2, dash="dash"),
                                    annotation_text=f"{key}: {str(threshold_value)}",
                                    annotation_position="right"
                                )
                            else:
                                print(f"Warning: No se pudo extraer un valor numérico del umbral '{key}' ({value}).")


            # **Caso 2: Agregar línea del MAE**
            if triggered_id == "add-performance-button" and model_selected and experiment_id["selected_experiment"] and param_values:
                fig = go.Figure(figure_data) if isinstance(figure_data, dict) else go.Figure()
                
                name_file_model = model_selector.get_configuration_by_model_name(model_selected)['ml_model_configuration']['model_description']['config_files']['model_file']
                name_prediction1 = generate_prediction_name(model_data_selected["model_file"])
                name_prediction2 = generate_prediction_name(name_file_model)
                df_bach = influxdb_handler.get_data_by_batch_id2(experiment_id["selected_experiment"])
                n = param_values[0]
                
                if name_prediction1 in df_bach.columns and name_prediction2 in df_bach.columns:
                    # Seleccionar los últimos `n` valores
                    y_true = df_bach[name_prediction1].iloc[-n:]
                    y_pred = df_bach[name_prediction2].iloc[-n:]

                    # Verificar si hay NaN y eliminarlos
                    df_valid = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
                    if df_valid.empty:
                        print("⚠️ Advertencia: Todos los valores contienen NaN, no se puede calcular la métrica.")
                        return fig

                    y_true = df_valid["y_true"]
                    y_pred = df_valid["y_pred"]

                    print("y_true", y_true.to_list())
                    print("y_pred", y_pred.to_list())
                    print("Métrica seleccionada:", selected_metric)

                    # Diccionario de métricas punto por punto
                    pointwise_metrics = {
                        "MAE": calculate_mae,
                        "MSE": calculate_mse,
                        "RMSE": calculate_rmse,
                        "VPD": calculate_vpd
                    }

                    # Diccionario de métricas globales (devuelven un solo valor)
                    constant_metrics = {
                        "PCC": calculate_pcc,
                        "CosSim": calculate_cossim,
                        "CV": calculate_cv
                    }

                    if selected_metric in pointwise_metrics:
                        metric_values = pointwise_metrics[selected_metric](y_true, y_pred)
                    elif selected_metric in constant_metrics:
                        metric_value = constant_metrics[selected_metric](y_true, y_pred)
                        metric_values = [metric_value] * len(y_true)  # Repetir en todos los puntos
                    else:
                        print(f"❌ Métrica '{selected_metric}' no soportada.")
                        return fig

                    # Manejar valores NaN (para PCC y CosSim) reemplazándolos por ceros
                    metric_values = np.nan_to_num(metric_values)

                    # Eliminar trazas anteriores de la misma métrica para evitar acumulaciones
                    fig.data = [trace for trace in fig.data if trace.name != f"{selected_metric} {name_prediction2}"]
                    # Obtener un nuevo color cada vez que se agrega una línea
                    color = get_next_color()

                    # Agregar la nueva traza de la métrica seleccionada
                    fig.add_trace(go.Scatter(
                        x=list(range(1, len(metric_values) + 1)),  # Posiciones 1, 2, ..., n
                        y=metric_values,
                        mode="lines+markers",
                        name=f"{selected_metric} {name_prediction2}",
                        line=dict(color=color, dash="dot"),  # Línea punteada
                        marker=dict(symbol="diamond", size=8, color=color)  # Rombo con color asignado
                    ))

                    # Configurar el diseño del gráfico
                    fig.update_layout(
                        xaxis=dict(title="Last elements"),
                        yaxis=dict(title=selected_metric),
                        yaxis_range=[0, max(metric_values) + 1] if selected_metric not in ["PCC", "CosSim"] else None,  # Ajuste solo si es necesario
                        legend=dict(
                            orientation="h",  # Leyenda en modo horizontal
                            yanchor="top",  # Anclaje superior
                            y=-0.2,  # Mueve la leyenda hacia abajo
                            xanchor="center",  # Centra la leyenda
                            x=0.5  # Posiciona la leyenda en el centro horizontal
                        )
                    )

            return fig
        