import dash
from dash.exceptions import PreventUpdate
from dash import html, dcc, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import re

from InfluxDb import influxdb_handler
from utils import model_selector
from utils.utils_performance_estimator import calculate_cossim,calculate_cv,calculate_mae,calculate_mse,calculate_pcc,calculate_rmse,calculate_vpd,get_next_color,generate_prediction_name
from utils.utils_global import disabled_figure


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
    print("value", selected_model)
    if selected_model:
        return model_selector.load_inputs_from_yaml(selected_model)
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
    metric_info = model_selector.load_estimator_descriptions(selected_metric)
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
def update_performance_plot(n_clicks, model_selected, experiment_id, model_data_selected, selected_metric, param_values, figure_data):
    global disabled_figure

    # Initialize the default figure
    fig = go.Figure(disabled_figure)

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Function to extract numerical values from thresholds
    def extract_threshold_value(text):
        numbers = re.findall(r"[-+]?\d*\.?\d+", text)  # Find numbers in the text
        return float(numbers[0]) if numbers else None  # Return the first number found

    # **Case 1: Add Thresholds**
    if triggered_id == "performance-estimator-dropdown" and selected_metric:
        fig = go.Figure()
        metric_info = model_selector.load_estimator_descriptions(selected_metric)
        if metric_info:
            # Define colors according to the threshold level
            threshold_colors = {"low": "green", "moderate": "orange", "high": "red"}
            thresholds = metric_info.get("method", {}).get("thresholds", {})
            # Extract threshold values
            low_threshold = extract_threshold_value(thresholds.get("low", ""))
            moderate_threshold = extract_threshold_value(thresholds.get("moderate", ""))
            high_threshold = extract_threshold_value(thresholds.get("high", ""))
            # Adjust the Y-axis limits for a wider range
            fig.update_layout(
                yaxis_range=[0, (high_threshold + 2)],  # Ensure the X-axis starts at 0
                margin=dict(l=0, r=70, t=10, b=10),  # Minimal margins
            )
            # Add colored areas
            if high_threshold is not None:
                fig.add_hrect(y0=high_threshold, y1=10,  # From high threshold to infinity
                              fillcolor="red", opacity=0.2, layer="below", line_width=0)

            if low_threshold is not None:
                fig.add_hrect(y0=-1, y1=low_threshold,  # From 0 to the low threshold
                              fillcolor="green", opacity=0.2, layer="below", line_width=0)

            # Add intermediate area (moderate) in orange
            if low_threshold is not None and high_threshold is not None:
                fig.add_hrect(y0=low_threshold, y1=high_threshold,  # Between both thresholds
                              fillcolor="orange", opacity=0.2, layer="below", line_width=0)
            # Add horizontal lines for thresholds
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
                        print(f"Warning: Could not extract a numerical value from the threshold '{key}' ({value}).")

    # **Case 2: Add MAE Line**
    if triggered_id == "add-performance-button" and model_selected and experiment_id["selected_experiment"] and param_values:
        fig = go.Figure(figure_data) if isinstance(figure_data, dict) else go.Figure()

        name_file_model = model_selector.get_configuration_by_model_name(model_selected)['ml_model_configuration']['model_description']['config_files']['model_file']
        name_prediction1 = generate_prediction_name(model_data_selected["model_file"])
        name_prediction2 = generate_prediction_name(name_file_model)
        df_bach = influxdb_handler.get_data_by_batch_id2(experiment_id["selected_experiment"])
        n = param_values[0]

        if name_prediction1 in df_bach.columns and name_prediction2 in df_bach.columns:
            # Select the last `n` values
            y_true = df_bach[name_prediction1].iloc[-n:]
            y_pred = df_bach[name_prediction2].iloc[-n:]

            # Check for NaN values and remove them
            df_valid = pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).dropna()
            if df_valid.empty:
                print("⚠️ Warning: All values contain NaN, unable to compute the metric.")
                return fig

            y_true = df_valid["y_true"]
            y_pred = df_valid["y_pred"]

            print("y_true", y_true.to_list())
            print("y_pred", y_pred.to_list())
            print("Selected metric:", selected_metric)

            # Dictionary of pointwise metrics
            pointwise_metrics = {
                "MAE": calculate_mae,
                "MSE": calculate_mse,
                "RMSE": calculate_rmse,
                "VPD": calculate_vpd
            }

            # Dictionary of global metrics (return a single value)
            constant_metrics = {
                "PCC": calculate_pcc,
                "CosSim": calculate_cossim,
                "CV": calculate_cv
            }

            if selected_metric in pointwise_metrics:
                metric_values = pointwise_metrics[selected_metric](y_true, y_pred)
            elif selected_metric in constant_metrics:
                metric_value = constant_metrics[selected_metric](y_true, y_pred)
                metric_values = [metric_value] * len(y_true)  # Repeat across all points
            else:
                print(f"❌ Metric '{selected_metric}' not supported.")
                return fig

            # Handle NaN values (for PCC and CosSim) by replacing them with zeros
            metric_values = np.nan_to_num(metric_values)

            # Remove previous traces of the same metric to avoid accumulation
            fig.data = [trace for trace in fig.data if trace.name != f"{selected_metric} {name_prediction2}"]
            # Get a new color each time a line is added
            color = get_next_color()

            # Add the new trace for the selected metric
            fig.add_trace(go.Scatter(
                x=list(range(1, len(metric_values) + 1)),  # Positions 1, 2, ..., n
                y=metric_values,
                mode="lines+markers",
                name=f"{selected_metric} {name_prediction2}",
                line=dict(color=color, dash="dot"),  # Dotted line
                marker=dict(symbol="diamond", size=8, color=color)  # Diamond marker with assigned color
            ))

            # Configure the chart layout
            fig.update_layout(
                xaxis=dict(title="Last elements"),
                yaxis=dict(title=selected_metric),
                yaxis_range=[0, max(metric_values) + 1] if selected_metric not in ["PCC", "CosSim"] else None,  # Adjust only if necessary
                legend=dict(
                    orientation="h",  # Horizontal legend mode
                    yanchor="top",  # Top anchor
                    y=-0.2,  # Move the legend downward
                    xanchor="center",  # Center the legend
                    x=0.5  # Position the legend at the horizontal center
                )
            )

    return fig
        