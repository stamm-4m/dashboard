import dash
import sys
from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
from dash import html
import plotly.graph_objs as go
import numpy as np
import scipy.stats as stats
import logging
from Dashboard.utils import model_information
from Dashboard.utils.utils_data_drift import get_result_metric,get_detector_description
from Dashboard.InfluxDb import influxdb_handler  # Retrieve the created instance

logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

UNIVARIABLE_METRICS = ["ADWIN","KS","PSI"]

# Load selected metrics
@dash.callback(
    Output("metrics-container", "children"),
    Output("graph-details", "style"),
    Input("metric-score-dropdown", "value"),
    State("soft-sensor-input", "value"),
    prevent_initial_call=True
)
def update_metrics_section(selected_metric, selected_model):
    print("selected_metric",selected_metric)
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
    print("method_params : ",method_params)
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
                                width=6,
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
                                width=6
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
                                ]), width=6, className="d-flex align-items-center"
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
                                ), width=6
                            )
                        ], className="mb-2")
                        for param_name, param_data in method_params.items()
                    ]
                ], width=6),

                # Right column: Description and thresholds well distributed
                dbc.Col([
                    html.H6("Metric Description", className="mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem(f"{key}: {value}") for key, value in metric_info.get("thresholds", {}).items()
                    ])
                ], width=6),
            ])
        ])
    ], className="mb-3 shadow-sm")
    return new_metric_section,graph_show

# Callback to generate density plots
@dash.callback(
    Output("density-plot", "figure"),
    Output("density-plot-hist", "figure"),
    Output("metrics-result", "children"),
    Input("add-metric-button", "n_clicks"),
    State("soft-sensor-input", "value"),
    State("input-experiment-dropdown", "value"),
    State("input-model-dropdown", "value"),
    State("metric-score-dropdown", "value"),
    Input("store-metric-params", "data"),
    prevent_initial_call=True
)
def update_density_plot(n_clicks, soft_sensor, experiment_id, selected_input, metric_score, param_dinamic_values):
    print("metric_score: ", metric_score)
    if not (soft_sensor and experiment_id):
        print("dash.no_update")
        return dash.no_update  # Prevent update if values are missing

    band_univariable = metric_score.strip() in UNIVARIABLE_METRICS
    print(band_univariable)
    print(selected_input)
    logging.warning(" values: band_univariable {band_univariable},  selected_input {selected_input}")

    if band_univariable and not selected_input:
        logging.warning(" No update: band_univariable and selected_input")
        return dash.no_update

    # 1. Retrieve data from the selected model's YAML
    config = model_information.get_configuration_by_model_name(soft_sensor)  # Implement this function
    training_info = config["training_information"]

    # 2. Extract values from experiments_id
    experiments_id = training_info.get("experiments_ID", {})
    print("training info experiments_id", experiments_id)
    if not experiments_id:
        return dash.no_update  # Prevent errors if no data is found
    print("param_dinamic_values",param_dinamic_values)
    if not param_dinamic_values or has_empty_values(param_dinamic_values):
        return dash.no_update  # Prevent errors if no data is found

    # 3. Query InfluxDB to obtain training and test data
    training_data = influxdb_handler.get_data_training(experiments_id, selected_input)  # Implement function
    test_data = influxdb_handler.get_data_test(experiment_id, selected_input)  # Implement function

    test_data = np.array(test_data).ravel()
    training_data = np.array(training_data).ravel()

    if len(training_data) == 0:
        noise = np.random.normal(0, 0.3, size=test_data.shape)
        training_data = test_data + noise

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
            title=f"Density of Training and Test Sets Histogram ({selected_input})",
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
        test_x, test_y = safe_kde(test_data, "red", "Test Set")
        fig2.add_trace(go.Scatter(
            x=test_x, y=test_y, mode='lines', name='Test Set',
            fill='tozeroy', line=dict(color='red', width=2), opacity=0.5
        ))

        fig2.update_layout(
            title=f"Density of Training and Test Sets ({selected_input})",
            xaxis_title=selected_input,
            yaxis_title="Density",
            template="plotly_white"
        )

    metric_result = get_result_metric(metric_score, training_data, test_data, param_dinamic_values)

    if band_univariable:
        return fig2, fig, render_dynamic_result(metric_result)
    else:
        return go.Figure(), go.Figure(), render_dynamic_result(metric_result)

@dash.callback(
    Output("store-metric-params", "data"),
    Input({'type': 'metric-param-input', 'metric': ALL, 'name': ALL}, 'value'),
    State({'type': 'metric-param-input', 'metric': ALL, 'name': ALL}, 'id'),
)
def process_dynamic_inputs(values, ids):
    grouped = {}
    for value, id_ in zip(values, ids):
        metric = id_.get('metric')
        name = id_.get('name')
        print(f"Métrica: {metric}, Parámetro: {name}, Valor: {value}")
        grouped.setdefault(metric, {})[name] = value
    return grouped

def render_dynamic_result(result, index=None):
    """
    Render any result object (dict-like) in a stylized Dash card.
    """
    # Convert to dictionary if needed
    if hasattr(result, "__dict__"):
        result_dict = result.__dict__
    elif isinstance(result, dict):
        result_dict = result
    else:
        #raise ValueError("Unsupported result type")
        return html.Pre(str(result))

    # Check for 'drift' key to style the card
    drift_value = result_dict.get("drift", False)
    color = "success" if drift_value else "danger"
    title = "Drift Detected ✅" if drift_value else "No Drift ❌"

    card_header = f"Result {index + 1}" if index is not None else "Drift Result"

    def render_key_value(key, value):
        if isinstance(value, dict):
            return html.Li(children=[
                f"{key}: ",
                html.Ul([html.Li(f"{k}: {v}") for k, v in value.items()])
            ])
        else:
            return html.Li(f"{key}: {value}")

    return dbc.Card(
        [
            dbc.CardHeader(card_header),
            dbc.CardBody([
                html.H5(title, className=f"text-{color}"),
                html.Ul([render_key_value(k, v) for k, v in result_dict.items()])
            ])
        ],
        className=f"border-{color} mb-3"
    )

def has_empty_values(params: dict) -> bool:
    """
    Check if there are any empty values in the nested dictionary.
    """
    return any(v == '' for subdict in params.values() for v in subdict.values())