import dash
from dash.exceptions import PreventUpdate
from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import re
import logging
from Dashboard.InfluxDb import influxdb_handler
from Dashboard.utils import model_information
from Dashboard.utils.utils_performance_estimator import get_next_color,reload_models,load_estimator_descriptions,compute_metric
from Dashboard.utils.utils_global import disabled_figure, generate_prediction_name
#from drift_detectors_pack.drift_detectors.drift_detector import DisagreementMetricLoader

        # Function to update the options of the existing models
@dash.callback(
            Output('soft-sensor-input-estimator', 'options'),
            Input('soft-sensor-input-estimator', 'n_clicks')
        )
def update_model_options(n_clicks):
    reload_models()
    return model_information.get_model_name_options()

@dash.callback(
            Output("performance-plot", "figure", allow_duplicate=True),
            Output("performance-estimator-container", "children",allow_duplicate=True),
            Output("soft-sensor-input-estimator", "value"),
            Output("performance-estimator-dropdown", "value"),  
            Output("metrics-table", "data",allow_duplicate=True),
            Output("metrics-table", "columns",allow_duplicate=True),
            Input("reset-performance-button", "n_clicks"),
            prevent_initial_call=True
)
def reset_performance_plot(n_clicks):
            global disabled_figure
            fig = go.Figure(disabled_figure)
            df = pd.DataFrame()
            return disabled_figure, html.Div(), "","", df.to_dict("records"), df.columns 

           

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
            Input('soft-sensor-input-estimator', 'value'),
            prevent_initial_call=True
)
def update_input_options(selected_model):
    print("value", selected_model)
    if selected_model:
        return model_information.load_inputs_from_configuration(selected_model)
    return []  # If no model is selected, leave it empty

# Load selected metrics
@dash.callback(
    Output("performance-estimator-container", "children"),
    Input("performance-estimator-dropdown", "value")
)
def update_estimator_section(selected_metric):
    if not selected_metric:
        return html.Div()  # If no metric is selected, return an empty div

    # Get information about the selected STIMAROE
    metric_info = load_estimator_descriptions(selected_metric)
    if not metric_info:
        return html.Div(html.P("No information available for this performance estimator."))

    threshold_colors = {"low": "success", "moderate": "warning", "high": "danger"}

    # Get the metric configuration parameters
    method_info = metric_info.get("method", {})
    formula = method_info.get("formula", "No formula available")
    thresholds = method_info.get("thresholds", {})
    method_params = metric_info.get("configuration", {}).get("method_parameters", [])
    implementation_notes = metric_info.get("implementation_notes", [])

    new_estimator_section = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                 dbc.Col([
                    html.H6("Performance estimator", className="mb-3"),  
                 ])
            ], className="mb-3 shadow-sm"), 
            dbc.Row([
                # Left column: Formula, parameters, and implementation notes
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

                # Right column: Thresholds with colors
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
         
# Agrega el valor obtenido del estimator para el modelo seleccionado y muestra los limites baj, medi  y alto para su error
# @dash.callback(
#             Output("performance-plot", "figure"),
#             Input("add-performance-button", "n_clicks"),
#             State("soft-sensor-input-estimator", "value"),  
#             Input("store-selected-state", "data"),
#             Input("model-data-store", "data"),
#             Input("performance-estimator-dropdown", "value"),  
#             State({"type": "dynamic-input", "index": ALL}, "value"),  
#             State("performance-plot", "figure"),  
#             prevent_initial_call=True
# )
# def update_performance_plot(n_clicks, model_selected, experiment_id, model_data_selected, selected_metric, param_values, figure_data):
#     """
#     Update the performance plot with thresholds and computed metrics.

#     This callback is triggered either when:
#     - The user selects a metric in the performance-estimator-dropdown (thresholds are added).
#     - The user clicks the add-performance-button (metric values are computed and added).

#     Workflow:
#     ----------
#     1. **Threshold Handling**:
#        - Extracts threshold values (low, moderate, high) from the selected metric description.
#        - Plots shaded regions in green, orange, and red corresponding to thresholds.
#        - Adds horizontal dashed lines with labels for threshold values.
#        - Adjusts y-axis limits to display all relevant values.

#     2. **Metric Computation and Plotting**:
#        - Retrieves true and predicted values from InfluxDB using the selected experiment.
#        - Selects the first `n` elements (defined in `param_values`).
#        - Cleans NaN values before computation.
#        - Computes the chosen metric (e.g., MAE).
#        - Removes any existing trace of the same metric to avoid duplicates.
#        - Plots the metric value as a scatter point with a unique color.
#        - Updates chart layout with axis labels, ranges, and legend positioning.

#     Parameters
#     ----------
#     n_clicks : int
#         Number of times the performance button was clicked.
#     model_selected : str
#         Name of the selected model from dropdown.
#     experiment_id : dict
#         Contains information about the selected experiment.
#     model_data_selected : dict
#         Metadata for the selected model.
#     selected_metric : str
#         Name of the metric chosen from dropdown.
#     param_values : list
#         Contains parameters; the first element defines number of elements `n`.
#     figure_data : dict or go.Figure
#         Current performance plot figure.

#     Returns
#     -------
#     go.Figure
#         Updated figure with thresholds and/or computed metric values.
#     """
#     global disabled_figure

#     # Initialize the default figure
#     fig = go.Figure(disabled_figure)

#     ctx = dash.callback_context
#     if not ctx.triggered:
#         raise PreventUpdate

#     triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

#     # Function to extract numerical values from thresholds
#     def extract_threshold_value(text):
#         numbers = re.findall(r"[-+]?\d*\.?\d+", text)  # Find numbers in the text
#         return float(numbers[0]) if numbers else None  # Return the first number found

#     # **Case 1: Add Thresholds**
#     if triggered_id == "performance-estimator-dropdown" and selected_metric:
#         fig = go.Figure()
#         metric_info = load_estimator_descriptions(selected_metric)
#         if metric_info:
#             # Define colors according to the threshold level
#             threshold_colors = {"low": "green", "moderate": "orange", "high": "red"}
#             thresholds = metric_info.get("method", {}).get("thresholds", {})
#             # Extract threshold values
#             low_threshold = extract_threshold_value(thresholds.get("low", ""))
#             moderate_threshold = extract_threshold_value(thresholds.get("moderate", ""))
#             high_threshold = extract_threshold_value(thresholds.get("high", ""))
#             # Adjust the Y-axis limits for a wider range
#             fig.update_layout(
#                 yaxis_range=[0, (high_threshold + 2)],  # Ensure the X-axis starts at 0
#                 margin=dict(l=0, r=70, t=10, b=10),  # Minimal margins
#             )
#             # Add colored areas
#             if high_threshold is not None:
#                 fig.add_hrect(y0=high_threshold, y1=10,  # From high threshold to infinity
#                               fillcolor="red", opacity=0.2, layer="below", line_width=0)

#             if low_threshold is not None:
#                 fig.add_hrect(y0=-10, y1=low_threshold,  # From 0 to the low threshold
#                               fillcolor="green", opacity=0.2, layer="below", line_width=0)

#             # Add intermediate area (moderate) in orange
#             if low_threshold is not None and high_threshold is not None:
#                 fig.add_hrect(y0=low_threshold, y1=high_threshold,  # Between both thresholds
#                               fillcolor="orange", opacity=0.2, layer="below", line_width=0)
#             # Add horizontal lines for thresholds
#             for key, value in thresholds.items():
#                 if key != "moderate" and key != "reference":
#                     threshold_value = extract_threshold_value(value)
#                     if threshold_value is not None:
#                         fig.add_hline(
#                             y=threshold_value,
#                             line=dict(color=threshold_colors.get(key, "black"), width=2, dash="dash"),
#                             annotation_text=f"{key}: {str(threshold_value)}",
#                             annotation_position="right"
#                         )
#                     else:
#                         print(f"Warning: Could not extract a numerical value from the threshold '{key}' ({value}).")

#     # **Case 2: Add MAE Line**
#     if triggered_id == "add-performance-button" and model_selected and experiment_id["selected_experiment"] and param_values:
#         fig = go.Figure(figure_data) if isinstance(figure_data, dict) else go.Figure()

#         name_file_model = model_information.get_configuration_by_model_name(model_selected)['model_description']['config_files']['model_file']
#         name_prediction1 = generate_prediction_name(model_data_selected["model_file"])
#         name_prediction2 = generate_prediction_name(name_file_model)
        
#         df_bach = influxdb_handler.get_data_by_batch_id2(experiment_id["selected_experiment"])
#         n = param_values[0]

#         if name_prediction1 in df_bach.columns and name_prediction2 in df_bach.columns:
#             # Select the last `n` values
#             #y_true = df_bach[name_prediction1].iloc[-n:]
#             #y_pred = df_bach[name_prediction2].iloc[-n:]
#             # Select the first n values
#             y_true = df_bach[name_prediction1].iloc[:n]
#             y_pred = df_bach[name_prediction2].iloc[:n]


#             # Check for NaN values and remove them
#             df_valid = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
#             if df_valid.empty:
#                 print("⚠️ Warning: All values contain NaN, unable to compute the metric.")
#                 return fig

#             y_true = df_valid["y_true"]
#             y_pred = df_valid["y_pred"]

#             #print("y_true", y_true.to_list())
#             #print("y_pred", y_pred.to_list())
#             print("Selected metric:", selected_metric)
            
#             metric_value = compute_metric(selected_metric,y_true,y_pred)
#             print("resultado:",metric_value)
#             mode = 'markers'  # o 'lines+markers' si quieres unir
            
#             if metric_value is None or metric_value == 0:
#                 print(f"⚠️ No metric values computed for {selected_metric}. Skipping plot.")
#                 return fig
#             #print(f"{metric.name} ({metric.acronym}): {value:.4f}")

#             # Remove previous traces of the same metric to avoid accumulation
#             fig.data = [trace for trace in fig.data if trace.name != f"{selected_metric} {name_prediction2}"]
#             # Get a new color each time a line is added
#             color = get_next_color()

#             # Add the new trace for the selected metric
#             fig.add_trace(go.Scatter(
#                 x=[n],  # Un solo valor X
#                 y=[metric_value],  # Un solo valor Y
#                 mode=mode,
#                 name=f"{selected_metric} {name_prediction2}",
#                 marker=dict(symbol="diamond", size=8, color=color)  # Diamond marker with assigned color
#             ))

#             # Configure the chart layout
#             fig.update_layout(
#                 xaxis=dict(title="Last elements"),
#                 yaxis=dict(title=selected_metric),
#                 yaxis_range=[
#                     min(0,float(np.min(metric_value))-10),  # Si hay negativos, muestra
#                     float(np.max(metric_value)) + 10
#                 ],
#                 legend=dict(
#                     orientation="h",
#                     yanchor="top",
#                     y=-0.2,
#                     xanchor="center",
#                     x=0.5
#                 )
#             )

#     return fig

@dash.callback(
    Output("performance-plot", "figure"),
    Input("add-performance-button", "n_clicks"),
    State("soft-sensor-input-estimator", "value"),  
    Input("store-selected-state", "data"),
    Input("model-data-store", "data"),
    Input("performance-estimator-dropdown", "value"),  
    State({"type": "dynamic-input", "index": ALL}, "value"),  
    State("performance-plot", "figure"),  
    prevent_initial_call=True
)
def update_performance_plot(n_clicks, model_selected, experiment_id, model_data_selected, selected_metric, param_values, figure_data):

    # Initialize the default figure
    fig = go.Figure(figure_data) if isinstance(figure_data, dict) else go.Figure()
    fig.layout = go.Layout()
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # **Case: Add performance lines**
    if triggered_id == "add-performance-button" and model_selected and experiment_id["selected_experiment"] and param_values:
       

        # Get model names
        name_file_model = model_information.get_configuration_by_model_name(model_selected)['model_description']['config_files']['model_file']
        name_prediction1 = generate_prediction_name(model_data_selected["model_file"])   # base model
        name_prediction2 = generate_prediction_name(name_file_model)                     # selected model

        existing_names = [trace.name for trace in fig.data]
        print("existing_names",existing_names)
        if name_prediction2 == name_prediction1 or name_prediction2 in existing_names:
            print(f"⚠️ {name_prediction2} exists not repeat.")
            return fig
        
        # Get experiment data
        df_bach = influxdb_handler.get_data_by_batch_id2(experiment_id["selected_experiment"])
        n = param_values[0]

        # Check both columns exist
        if name_prediction1 in df_bach.columns and name_prediction2 in df_bach.columns:
            # Select the first n values
            y_true = df_bach[name_prediction1].iloc[:n]
            y_pred = df_bach[name_prediction2].iloc[:n]

            # Clean NaNs
            df_valid = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
            if df_valid.empty:
                print("⚠️ Warning: All values contain NaN, unable to compute.")
                return fig

            y_true = df_valid["y_true"]
            y_pred = df_valid["y_pred"]
            existing_names = [trace.name for trace in fig.data]

            # Add trace for base model only if not already in the figure
            if name_prediction1 not in existing_names:
                color1 = get_next_color()
                fig.add_trace(go.Scatter(
                    x=list(range(len(y_true))),
                    y=y_true,
                    mode="lines+markers",
                    name=name_prediction1,
                    marker=dict(symbol="circle", size=6, color=color1)
                ))

            # Add trace for selected model only if not already in the figure
            if name_prediction2 not in existing_names:
                color2 = get_next_color()
                fig.add_trace(go.Scatter(
                    x=list(range(len(y_pred))),
                    y=y_pred,
                    mode="lines+markers",
                    name=name_prediction2,
                    marker=dict(symbol="diamond", size=6, color=color2)
                ))


            # Layout config
            fig.update_layout(
                xaxis=dict(title=f"First {n} elements"),
                yaxis=dict(title=selected_metric),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )

    return fig

@dash.callback(
    Output("metrics-table", "data"),
    Output("metrics-table", "columns"),
    Input("add-performance-button", "n_clicks"),
    Input("soft-sensor-input-estimator", "value"),
    State("store-selected-state", "data"),
    State("model-data-store", "data"),
    State("metrics-table", "data"),
    State({"type": "dynamic-input", "index": ALL}, "value"),
    Input("performance-estimator-dropdown", "value"),
    prevent_initial_call=True
)
def update_metrics_table(click_n, model_selected, experiment_id, model_data_selected, existing_data, param_values, metric_selected):
    if not model_selected or not model_data_selected or not experiment_id:
        return dash.no_update, dash.no_update

    # ✅ Obtener nombres de predicciones
    name_file_model = model_information.get_configuration_by_model_name(model_selected)['model_description']['config_files']['model_file']
    name_prediction1 = generate_prediction_name(model_data_selected["model_file"])
    name_prediction2 = generate_prediction_name(name_file_model)

    if name_prediction1 == name_prediction2:
        return dash.no_update, dash.no_update

    df_bach = influxdb_handler.get_data_by_batch_id2(experiment_id["selected_experiment"])

    if name_prediction1 in df_bach.columns and name_prediction2 in df_bach.columns and param_values:
        n = param_values[0]
        y_true = df_bach[name_prediction1].iloc[:n]
        y_pred = df_bach[name_prediction2].iloc[:n]

        # ✅ Eliminar NaN
        df_valid = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
        if df_valid.empty:
            return dash.no_update, dash.no_update

        y_true = df_valid["y_true"]
        y_pred = df_valid["y_pred"]

        # ✅ Calcular métrica seleccionada
        result = compute_metric(metric_selected, y_true, y_pred)
        result = round(result, 4)

        # ✅ Reconstruir DataFrame pivotado
        if existing_data and len(existing_data) > 0:
            df_table = pd.DataFrame(existing_data)
            df_table.set_index("Metric", inplace=True)
        else:
            # Crear estructura inicial si no existe
            df_table = pd.DataFrame(columns=[model_selected])
            df_table.index.name = "Metric"

        # ✅ Asegurar que la fila (métrica) exista
        if metric_selected not in df_table.index:
            df_table.loc[metric_selected] = [None] * len(df_table.columns)

        # ✅ Asegurar que la columna (modelo) exista
        if model_selected not in df_table.columns:
            df_table[model_selected] = None

        # ✅ Asignar valor
        df_table.loc[metric_selected, model_selected] = result

        # ✅ Reset index para DataTable
        df_table.reset_index(inplace=True)

        columns = [{"name": col, "id": col} for col in df_table.columns]

        return df_table.to_dict("records"), columns

    return dash.no_update, dash.no_update
