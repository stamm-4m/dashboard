import dash
from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np
import scipy.stats as stats

from utils import model_information
from utils.utils_data_drift import get_result_metric,get_detector_description
from InfluxDb import influxdb_handler  # Retrieve the created instance

UNIVARIABLE_METRICS = ["Adwin","KSDetector","PSI"]

# Load selected metrics
@dash.callback(
    Output("metrics-container", "children"),
    Output("graph-details", "style"),
    Input("metric-score-dropdown", "value"),
    State("soft-sensor-input", "value"),
    prevent_initial_call=True
)
def update_metrics_section(selected_metric, selected_model):
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
    method_params = metric_info.get("configuration", {}).get("method_parameters", [])
    
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
                                    f"{param.get('name', 'unknown')}",
                                    html.Span(" ⓘ", id=f"tooltip-{selected_metric.strip()}-{param.get('name', 'unknown')}",
                                            style={"textDecoration": "underline dotted", "cursor": "help"}),
                                    dbc.Tooltip(
                                        param.get('description', 'No description available'),
                                        target=f"tooltip-{selected_metric.strip()}-{param.get('name', 'unknown')}"
                                    )
                                ]), width=6, className="d-flex align-items-center"
                            ),
                            dbc.Col(
                                dcc.Input(
                                    id={
                                        'type': 'metric-param-input',
                                        'metric': selected_metric.strip(),
                                        'name': param.get('name', 'unknown')
                                    },
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
def update_density_plot(n_clicks, soft_sensor, experiment_id, selected_input,metric_score,param_dinamic_values):
    if not (soft_sensor and experiment_id and selected_input):
        print("dash.no_update")
        return dash.no_update  # Prevent update if values are missing
    
    # 1. Retrieve data from the selected model's YAML
    config = model_information.get_configuration_by_model_name(soft_sensor)  # Implement this function
    training_info = config["training_information"]

    # 2. Extract values from experiments_id
    experiments_id = training_info.get("experiments_ID", {})
    print("training info experiments_id", experiments_id)
    if not experiments_id:
        return dash.no_update  # Prevent errors if no data is found

    # 3. Query InfluxDB to obtain training and test data
    training_data = influxdb_handler.get_data_training(experiments_id, selected_input)  # Implement function
    test_data = influxdb_handler.get_data_test(experiment_id, selected_input)  # Implement function

    # Create copy to generate random test data
    if len(training_data) == 0:
        if isinstance(test_data, list):
            test_d = np.array(test_data)
            noise = np.random.normal(0, 0.1, size=test_d.shape)
            training_data = test_d + noise
    print("Data:")
    #print("training_data", training_data)
    #print("test_data", test_data)

    # 4. Create density plot
    fig = go.Figure()

    # KDE for Training Set
    fig.add_trace(go.Histogram(
        x=training_data, histnorm='probability density', name='Training Set',
        opacity=0.5, marker=dict(color='blue')
    ))

    # KDE for Test Set
    fig.add_trace(go.Histogram(
        x=test_data, histnorm='probability density', name='Test Set',
        opacity=0.5, marker=dict(color='red')
    ))

    # Layout of the graph
    fig.update_layout(
        title=f"Density of Training and Test Sets Histogram ({selected_input})",
        xaxis_title=selected_input,
        yaxis_title="Density",
        barmode="overlay",  # Overlay both distributions
        template="plotly_white"
    )

    fig2 = go.Figure()
    
    # Compute KDE for Training Set
    train_kde = stats.gaussian_kde(training_data)
    train_x = np.linspace(min(training_data), max(training_data), 100)
    train_y = train_kde(train_x)

    # Compute KDE for Test Set
    test_kde = stats.gaussian_kde(test_data)
    test_x = np.linspace(min(test_data), max(test_data), 100)
    test_y = test_kde(test_x)

    # Add KDE for Training Set as area
    fig2.add_trace(go.Scatter(
        x=train_x, y=train_y, mode='lines', name='Training Set',
        fill='tozeroy', line=dict(color='blue', width=2), opacity=0.5
    ))

    # Add KDE for Test Set as area
    fig2.add_trace(go.Scatter(
        x=test_x, y=test_y, mode='lines', name='Test Set',
        fill='tozeroy', line=dict(color='red', width=2), opacity=0.5
    ))

    # Layout of the graph
    fig2.update_layout(
        title=f"Density of Training and Test Sets ({selected_input})",
        xaxis_title=selected_input,
        yaxis_title="Density",
        template="plotly_white"
    )
    
    metric_result = get_result_metric(metric_score,training_data,test_data,param_dinamic_values)
    metric_result = html.H2(f" {metric_score} = {metric_result}")

    return fig2, fig, metric_result

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