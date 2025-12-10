import dash
import sys
from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from dash import html
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import scipy.stats as stats
import logging
import json
from Dashboard.utils import model_information
from Dashboard.utils.utils_data_drift import get_result_metric,get_detector_description
from Dashboard.utils.utils_sofsensors_offline import reload_models
from Dashboard.InfluxDb import influxdb_handler  # Retrieve the created instance

logger = logging.getLogger(__name__)


UNIVARIABLE_METRICS = ["ADWIN","KS","PSI"]

@dash.callback(
    Output('soft-sensor-input', 'options'),
    Input('soft-sensor-input', 'n_clicks')
)
def reload_model_options(n_clicks):
    reload_models()
    return model_information.get_model_name_options()

# Load selected metrics
@dash.callback(
    Output("metrics-container", "children"),
    Output("graph-details", "style"),
    Input("metric-score-dropdown", "value"),
    State("soft-sensor-input", "value"),
    prevent_initial_call=True
)
def update_metrics_section(selected_metric, selected_model):
    logger.debug(f"selected_metric: {selected_metric}")
    if not selected_metric:
        return html.Div(),{"display": "none"}  # If no metric is selected, return an empty div,# If no model is selected, leave it empty
    
    model_options = [] # If no model is selected, leave it empty
    if selected_model:
        model_options = model_information.load_inputs_from_configuration(selected_model)
    variable_show = {"display":"none"}
    graph_show = {"display":"none"}
    if selected_metric.strip() in UNIVARIABLE_METRICS:
        variable_show = {"display":"block"}
        graph_show = {"display":"block"}

    # Get information about the selected metric
    metric_info = get_detector_description(selected_metric)
    if not metric_info:
        return html.Div(html.P("No information available for this metric."))

    # Get metric configuration parameters
    method_params = metric_info.get("configuration", {})
    logger.debug("configuration method_params : {method_params}")
    # Dynamically build inputs
    inputs = []
    new_metric_section = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Left column: Aligned inputs
                dbc.Col([
                    html.H6("Metric Parameters"),
                    html.Div(
                        id="variable-section",
                        style=variable_show,
                        children=[
                        dbc.Row([
                            dbc.Col(
                                html.Label("Variable"),
                                width=4,
                                className="d-flex align-items-center"
                            ),
                            dbc.Col(
                                dcc.Dropdown(
                                    id='input-model-dropdown',
                                    options=model_options,
                                    searchable=True,
                                    placeholder="Select Input Model",
                                    style={'width': '100%'}
                                ),
                                width=8
                            )
                        ], className="mb-2")
                    ]
                    ),
                    *[
                        dbc.Row([

                            dbc.Col(
                               html.Label([
                                    f"{param_name}",
                                    html.Span(" ⓘ", id=f"tooltip-{selected_metric.strip()}-{param_name}",
                                            style={"textDecoration": "underline dotted", "cursor": "help"}),
                                    dbc.Tooltip(
                                        param_data.get('description', 'No description available'),
                                        target=f"tooltip-{selected_metric.strip()}-{param_name}"
                                    )
                                ]), width=4, className="d-flex align-items-center"
                            ),
                            dbc.Col(
                                dcc.Input(
                                    id={
                                        'type': 'metric-param-input',
                                        'metric': selected_metric.strip(),
                                        'name': param_name
                                    },
                                    type="text",
                                    value=param_data.get('default', ''),
                                    className="mb-2",
                                    style={'width': '100%'}
                                ), width=8
                            )
                        ], className="mb-2")
                        for param_name, param_data in method_params.items()
                    ]
                ], width=5),

                # Right column: Description and thresholds well distributed
                dbc.Col([
                    dbc.Row(
                        [
                        ],id="metrics-result"
                        )
                ], width=7),
            ])
        ])
    ], className="mb-3 shadow-sm")
    return new_metric_section,graph_show

# Callback to generate density plots
@dash.callback(
    Output("density-plot", "figure"),
    #Output("density-plot-hist", "figure"),
    Output("metrics-result", "children"),
    Input("add-metric-button", "n_clicks"),
    State("soft-sensor-input", "value"),
    State("input-experiment-dropdown", "children"),
    State("input-model-dropdown", "value"),
    State("metric-score-dropdown", "value"),
    Input("store-metric-params", "data"),
    Input("time-window-size-drift", "value"),
    prevent_initial_call=True
)
def update_density_plot(n_clicks, soft_sensor, experiment_id, selected_input, metric_score, param_dinamic_values,range_slider):
    logger.debug(f"metric_score: {metric_score}")
    if not (soft_sensor and experiment_id):
        logger.warning("dash.no_update not soft sensor and experiment id")
        return dash.no_update  # Prevent update if values are missing

    band_univariable = metric_score.strip() in UNIVARIABLE_METRICS

    logger.debug(f"values: band_univariable {band_univariable},  selected_input {selected_input}")

    if band_univariable and not selected_input:
        logger.warning(" No update: band_univariable and selected_input")
        return dash.no_update

    # 1. Retrieve data from the selected model's YAML
    config = model_information.get_configuration_by_model_name(soft_sensor)  # Implement this function
    training_info = config["training_information"]

    # 2. Extract values from experiments_id
    experiments_id = training_info.get("experiments_ID", {})
    logger.debug(f"training info experiments_id {experiments_id}")
    if not experiments_id:
        return dash.no_update  # Prevent errors if no data is found
    logger.debug(f"param_dinamic_values {param_dinamic_values}")
    if not param_dinamic_values or has_empty_values(param_dinamic_values):
        return dash.no_update  # Prevent errors if no data is found

    # 3. Query InfluxDB to obtain training and test data
    training_data = influxdb_handler.get_data_training(experiments_id, selected_input)  # Implement function
    test_data = influxdb_handler.get_data_test(experiment_id, selected_input,range_slider)  # Implement function

    test_data = np.array(test_data).ravel()
    training_data = np.array(training_data).ravel()
    #logger.debug(f"training_data: \n {training_data}")
    #logger.debug(f"test_data: \n {test_data}")
    # CAUTION: is only for test when no exists any trainig data
    # --------------------------------------------------------- 
    if len(training_data) == 0:
        noise = np.random.normal(0, 0.3, size=test_data.shape)
        training_data = test_data + noise
    # --------------------------------------------------------- 

    fig = go.Figure()
    fig2 = go.Figure()

    if band_univariable:
        # Histogramas
        fig.add_trace(go.Histogram(
            x=training_data, histnorm='probability density', name='Training Set',
            opacity=0.5, marker=dict(color='blue')
        ))
        fig.add_trace(go.Histogram(
            x=test_data, histnorm='probability density', name='Test Set',
            opacity=0.5, marker=dict(color='red')
        ))
        fig.update_layout(
            title=f"Density of training set and Experiment ID {experiment_id} - Variable ({selected_input})",
            xaxis_title=selected_input,
            yaxis_title="Density",
            barmode="overlay",
            template="plotly_white"
        )

        # === KDE o manejo de datos constantes ===
        def safe_kde(data, color, name):
            if np.var(data) < 1e-6:  # casi constante
                const_val = float(np.mean(data))
                x_vals = np.linspace(const_val - 1, const_val + 1, 100)
                y_vals = np.zeros_like(x_vals)
                y_vals[len(y_vals)//2] = 1.0  # pico artificial
                return x_vals, y_vals
            else:
                kde = stats.gaussian_kde(data)
                x_vals = np.linspace(min(data), max(data), 100)
                y_vals = kde(x_vals)
                return x_vals, y_vals

        # Training KDE
        train_x, train_y = safe_kde(training_data, "blue", "Training Set")
        fig2.add_trace(go.Scatter(
            x=train_x, y=train_y, mode='lines', name='Training Set',
            fill='tozeroy', line=dict(color='blue', width=2), opacity=0.5
        ))

        # Test KDE
        test_x, test_y = safe_kde(test_data, "red", f"Experiment ID: {experiment_id}")
        fig2.add_trace(go.Scatter(
            x=test_x, y=test_y, mode='lines', name=f"Experiment ID: {experiment_id}",
            fill='tozeroy', line=dict(color='red', width=2), opacity=0.5
        ))

        fig2.update_layout(
            title=f"Density of training set and Experiment ID: {experiment_id} - Variable: {selected_input}",
            xaxis_title=selected_input,
            yaxis_title="Density",
            template="plotly_white"
        )

    dfo = influxdb_handler.get_data_by_batch_id(experiment_id,5)
    str_mode = False
    if not dfo.empty:
        str_mode = True

    metric_result = get_result_metric(metric_score, training_data, test_data, param_dinamic_values,str_mode)

    if band_univariable:
        #return fig2, fig, render_dynamic_result(metric_result)
        return fig2, render_dynamic_result(metric_result)
    else:
        #return go.Figure(), go.Figure(), render_dynamic_result(metric_result)
        return go.Figure(), render_dynamic_result(metric_result)

@dash.callback(
    Output("store-metric-params", "data"),
    Input({'type': 'metric-param-input', 'metric': ALL, 'name': ALL}, 'value'),
    State({'type': 'metric-param-input', 'metric': ALL, 'name': ALL}, 'id'),
    State('url', 'pathname'),
)
def process_dynamic_inputs(values, ids, pathname):
    """
    Processes dynamic metric parameter inputs from the user interface.
    Groups parameters by metric and updates only when all required parameters
    for a metric are filled.
    """
    #logger.debug(f"pathname: {pathname}")
    if pathname != "/monitoring/data-drift":  # o la ruta real
        return dash.no_update
    
    if not values or not ids:
        logger.debug("No data received for metric parameters.")
        return dash.no_update

    grouped = {}

    # Organize all parameters by metric
    for value, id_ in zip(values, ids):
        metric = id_.get("metric")
        name = id_.get("name")
        grouped.setdefault(metric, {})[name] = value

    # Check that every parameter for every metric is filled
    all_complete = True
    for metric, params in grouped.items():
        if any(v in (None, "", []) for v in params.values()):
            logger.debug(f"Metric {metric} is incomplete: {params}")
            all_complete = False
            break

    if not all_complete:
        logger.debug("Not all metric parameters are filled; skipping update.")
        return dash.no_update

    logger.debug(f"All metric parameters complete: {grouped}")
    return grouped

def render_dynamic_result(result, index=None):
    """
    Render any result object (dict-like) in a stylized Dash card.
    Adds human-readable explanation for ADWIN drift detector outputs.
    """

    # Convert to dictionary if needed
    if hasattr(result, "__dict__"):
        result_dict = result.__dict__
    elif isinstance(result, dict):
        result_dict = result
    else:
        return html.Pre(str(result))

    # ------------------------------------------------------------------
    # Detect main drift flag
    # ------------------------------------------------------------------
    drift_value = result_dict.get("drift", False)
    title = "Drift Detected ✅" if drift_value else "No Drift ❌"
    card_header = f"Result {index + 1}" if index is not None else "Drift Result"

    # ------------------------------------------------------------------
    # Build human-readable explanation
    # ------------------------------------------------------------------
    explanation_items = []

    # (1) drift
    if drift_value:
        explanation_items.append("ADWIN detected a real change in the data.")
    else:
        explanation_items.append("ADWIN found no change in the data.")

    color = "success" if drift_value else "danger"
    # (2) last_index
    li = result_dict.get("last_index", -1)
    if li >= 0:
        explanation_items.append(f"The drift was detected at position {li} in the stream.")
    else:
        explanation_items.append("No drift location was detected in the stream.")

    # (3) details → delta + mode (in an indented block)
    details_dict = result_dict.get("details", {})
    if isinstance(details_dict, dict):
        explanation_items.append(
            html.Div([
                "Used parameters:",
                html.Pre(
                    (
                        ("    delta: This is a sensitivity parameter.\n" if "delta" in details_dict else "")
                        +
                        ("    mode: It was running in online mode." if "mode" in details_dict else "")
                    )
                )
            ])
        )

    # Convert explanation list to HTML
    explanation_block = html.Div(
        [
            html.Ul([
                html.Li(item) if isinstance(item, str) else html.Li(item)
                for item in explanation_items
            ])
        ]
    )

    # ------------------------------------------------------------------
    # Render the raw key/value dictionary
    # ------------------------------------------------------------------
    def render_key_value(key, value):
        if isinstance(value, dict):
            return html.Li(children=[
                f"{key}: ",
                html.Ul([html.Li(f"{k}: {v}") for k, v in value.items()])
            ])
        else:
            return html.Li(f"{key}: {value}")

    return (
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(html.H6("Explanation")),
                    dbc.CardBody([explanation_block])
                ],
                className=f"border-{color} mb-3"
            ),
            width=7,className="align-items-center"
        ),
        dbc.Col(
            dbc.Card(
                [
                    dbc.CardHeader(html.H6(card_header)),
                    dbc.CardBody(
                        [
                            html.H5(title, className=f"text-{color}"),
                            html.Ul([render_key_value(k, v) for k, v in result_dict.items()])
                        ]
                    )
                ],
                className=f"border-{color} mb-3"
            ),
            width=5, className="align-items-center"
        )
    )


def has_empty_values(params: dict) -> bool:
    """
    Check if there are any empty values in the nested dictionary.
    """
    return any(v == '' for subdict in params.values() for v in subdict.values())


@dash.callback(
    Output("time-ws-slider-labels-drift", "children"),
    Output("time-window-size-drift", "max"),
    Input("store-selected-state", "data"),
    Input("time-window-size-drift", "value")
)
def update_size_slider_labels(data, slider_range):
    """
    Update the labels and maximum value of the time window slider 
    based on available data for the selected experiment.

    Behavior:
        - If no experiment is selected, the function returns an empty label and 0.
        - First, it attempts to fetch online data (last 5 minutes).
            * Displays total number of elements available online.
            * Shows start and end times according to the slider range.
            * Displays the number of elements selected within the slider window.
        - If no online data is found, it falls back to batch data.
            * Displays total number of elements in the batch.
            * Shows start and end times according to the slider range.
            * Displays the number of elements selected within the slider window.
        - If no data is found at all, it returns an empty label and 0.

    Args:
        data (dict): Dash store state, expected to contain the selected experiment ID.
        slider_range (list[int]): The [start, end] indices of the slider selection.

    Returns:
        tuple:
            - str: The label describing the time range and number of elements.
            - int: The maximum slider value (total number of available timestamps).
    """
    if not data or "selected_experiment" not in data or not data["selected_experiment"]:
        logger.info("No experiment ID Selected")
        return "", 0
    
    # Consulta últimos datos online (últimos 5 min)
    dfc = influxdb_handler.get_data_by_batch_id(data['selected_experiment'], 5)

    if not dfc.empty:
        timestamps = sorted(dfc["_time"].dropna().unique())
        n_total = len(timestamps)

        # Ajustar con slider
        start_idx, end_idx = slider_range
        start_time = timestamps[start_idx] if start_idx < n_total else timestamps[0]
        end_time = timestamps[end_idx] if end_idx < n_total else timestamps[-1]

        start_str = pd.to_datetime(start_time).strftime('%Y-%m-%d %H:%M:%S')
        end_str = pd.to_datetime(end_time).strftime('%Y-%m-%d %H:%M:%S')

        # Número de elementos en la selección del slider
        n_selected = end_idx - start_idx if end_idx >= start_idx else 0

        return [
            f"Last {n_total} elements - Selected {n_selected}",
            html.Br(),
            f"➡ From: {start_str} To: {end_str}"
        ], n_total

    # Si no hay datos online, se consulta batch completo
    dfc = influxdb_handler.get_data_by_batch_id(data['selected_experiment'])
    if not dfc.empty:
        timestamps = sorted(dfc["_time"].dropna().unique())
        n_total = len(timestamps)

        start_idx, end_idx = slider_range
        start_time = timestamps[start_idx] if start_idx < n_total else timestamps[0]
        end_time = timestamps[end_idx] if end_idx < n_total else timestamps[-1]

        start_str = pd.to_datetime(start_time).strftime('%Y-%m-%d %H:%M:%S')
        end_str = pd.to_datetime(end_time).strftime('%Y-%m-%d %H:%M:%S')

        n_selected = end_idx - start_idx if end_idx >= start_idx else 0

        return [f"From: {start_str} ➡ To: {end_str}",
                html.Br(),
                f"- Selected {n_selected}"
        ], n_total
    
    return "", 0

@dash.callback(
    Output("input-experiment-dropdown", "children"),
    Input("store-selected-state", "data"),
    prevent_initial_call=False 
)
def load_selected_experiment(store_data):
    """
    Load the stored experiment ID into the dropdown on app load.
    """
    if store_data and "selected_experiment" in store_data:
        return store_data["selected_experiment"]
    return None
