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
from Dashboard.utils.utils_performance_estimator import get_next_color,reload_models,load_estimator_descriptions,compute_metric,reorder_dataframe_for_table
from Dashboard.utils.utils_global import disabled_figure

logger = logging.getLogger(__name__) 

# Function to update the options of the existing models
@dash.callback(
            Output('soft-sensor-input-estimator', 'options'),
            Input('soft-sensor-input-estimator', 'n_clicks')
        )
def update_model_options(n_clicks):
    reload_models()
    return model_information.get_model_id_options()

@dash.callback(
            Output("performance-plot", "figure", allow_duplicate=True),
            Output("performance-estimator-container", "children",allow_duplicate=True),
            Output("soft-sensor-input-estimator", "value"),
            Output("performance-estimator-dropdown", "value"),  
            Output("metrics-table", "data",allow_duplicate=True),
            Output("metrics-table", "columns",allow_duplicate=True),
            Output("time-window-size", "value",allow_duplicate=True),
            Input("reset-performance-button", "n_clicks"),
            prevent_initial_call=True
)
def reset_performance_plot(n_clicks):
            global disabled_figure
            fig = go.Figure(disabled_figure)
            df = pd.DataFrame()
            return disabled_figure, html.Div(), "","", df.to_dict("records"), df.columns,[0, 100] 

           

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
                                    html.Span(" ⓘ", id=f"tooltip-{selected_metric.strip()}-{param.get('name', 'unknown')}",
                                            style={"textDecoration": "underline dotted", "cursor": "help"}),
                                    dbc.Tooltip(
                                        param.get('description', 'No description available'),
                                        target=f"tooltip-{selected_metric.strip()}-{param.get('name', 'unknown')}"
                                    )
                                ]), width=6, className="d-flex align-items-center"
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
    State("soft-sensor-input-estimator", "value"),
    Input("store-selected-state", "data"),
    Input("model-data-store", "data"),
    Input("time-window-size", "value"),
    State("performance-plot", "figure"),
    prevent_initial_call=True
)
def update_performance_plot(n_clicks, models_selected, experiment_id, model_data_selected, range_slider, figure_data):

    # Initialize the default figure
    fig = go.Figure(figure_data) if isinstance(figure_data, dict) else go.Figure()
    fig.layout = go.Layout()
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if not (models_selected and experiment_id["selected_experiment"] and range_slider):
        return fig

    # Nombre del modelo base
    base_pred_name = model_data_selected["model_id"]   # base model

    # Data del experimento
    df_bach = influxdb_handler.get_data_by_batch_id(experiment_id["selected_experiment"])

    if "_time" not in df_bach.columns:
        print("⚠️ _time column missing in data")
        return fig

    # Asegurar datetime
    df_bach["_time"] = pd.to_datetime(df_bach["_time"], utc=True).dt.tz_localize(None)
    df_bach = df_bach.sort_values("_time")

    timestamps = df_bach["_time"].tolist()
    logger.info(f"range_slider: {range_slider}")
    if range_slider[0] < 0 or range_slider[1] > len(timestamps):
        print("⚠️ Invalid time window indices")
        return fig

    start_time = timestamps[range_slider[0]]
    end_time = timestamps[range_slider[1]-1]
    df_window = df_bach[(df_bach["_time"] >= start_time) & (df_bach["_time"] <= end_time)]
    if df_window.empty:
        print("⚠️ No data in selected window")
        return fig

    # 🔹 MODE 1: Update traces when time window changes
    logger.info(f"triggered_id: {triggered_id}")
    if triggered_id == "time-window-size":
        new_data = []
        for trace in fig.data:
            model_name = trace.name
            if model_name not in df_window.columns:
                print(f"⚠️ {model_name} not found in window data")
                continue

            df_valid = pd.DataFrame({"_time": df_window["_time"], "y": df_window[model_name]}).dropna()

            new_trace = go.Scatter(
                x=df_valid["_time"],
                y=df_valid["y"],
                mode=trace.mode,
                name=model_name,
                marker=trace.marker,
                hovertemplate=trace.hovertemplate
            )
            new_data.append(new_trace)

        fig = go.Figure(data=new_data, layout=fig.layout)
        # Layout config
        fig.update_layout(
            xaxis=dict(title="Time"),
            yaxis=dict(hoverformat=".2f"),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            hovermode="x unified"
        )

        return fig

    # 🔹 MODE 2: Add new traces when button is pressed
    if triggered_id == "add-performance-button":
        # Base trace
        if base_pred_name in df_window.columns:
            existing_names = [trace.name for trace in fig.data]
            if base_pred_name not in existing_names:
                color1 = get_next_color()
                fig.add_trace(go.Scatter(
                    x=df_window["_time"],
                    y=df_window[base_pred_name],
                    mode="lines+markers",
                    name=base_pred_name,
                    marker=dict(symbol="circle", size=6, color=color1),
                    hovertemplate="<br>%{fullData.name}: %{y}<extra></extra>"
                ))

        # Add selected models
        logger.debug(f"models_selected :\n {models_selected}")
        for model_selected in models_selected:
            pred_name = model_information.get_configuration_by_model_name(model_selected)['model_identification']['ID']
            logger.debug(f"model_selected:\n {pred_name}")
            
            if pred_name == base_pred_name:
                continue

            existing_names = [trace.name for trace in fig.data]
            if pred_name in existing_names:
                continue

            if pred_name not in df_window.columns:
                print(f"⚠️ {pred_name} not found in data.")
                continue

            df_valid = pd.DataFrame({"_time": df_window["_time"], "y": df_window[pred_name]}).dropna()
            if df_valid.empty:
                continue

            color2 = get_next_color()
            fig.add_trace(go.Scatter(
                x=df_valid["_time"],
                y=df_valid["y"],
                mode="lines+markers",
                name=pred_name,
                marker=dict(symbol="diamond", size=6, color=color2),
                hovertemplate="<br>%{fullData.name}: %{y}<extra></extra>"
            ))

    # Layout config
    fig.update_layout(
        xaxis=dict(title="Time"),
        yaxis=dict(hoverformat=".2f"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified"
    )

    return fig

@dash.callback(
    Output("metrics-table", "data"),
    Output("metrics-table", "columns"),
    Output("metrics-table", "style_data_conditional"),
    State("soft-sensor-input-estimator", "value"),  # ahora lista (multi-select)
    State("store-selected-state", "data"),
    State("model-data-store", "data"),
    State("metrics-table", "data"),
    Input("time-window-size", "value"),            # ✅ reemplaza dynamic-input
    Input("performance-estimator-dropdown", "value"),
    prevent_initial_call=True
)
def update_metrics_table(models_selected, experiment_id, model_data_selected, existing_data, range_slider, metric_selected):
    print(f"range_slider: {range_slider}")
    if not models_selected or not model_data_selected or not experiment_id or not range_slider or not metric_selected:
        return dash.no_update, dash.no_update, dash.no_update
    
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print("triggered_id : ",triggered_id)

    # ✅ Obtener datos
    df_bach = influxdb_handler.get_data_by_batch_id(experiment_id["selected_experiment"])
    if "_time" not in df_bach.columns:
        return dash.no_update, dash.no_update, dash.no_update

    # Asegurar datetime
    df_bach["_time"] = pd.to_datetime(df_bach["_time"], utc=True).dt.tz_localize(None)
    df_bach = df_bach.sort_values("_time").reset_index(drop=True)

    # Validar indices del slider
    start_idx, end_idx = range_slider
    if start_idx < 0 or end_idx >= len(df_bach):
        return dash.no_update, dash.no_update, dash._no_update
    print(f'df_bach.iloc[start_idx:end_idx+1]: {df_bach.iloc[start_idx:end_idx+1]}')
    df_window = df_bach.iloc[start_idx:end_idx+1]
    if df_window.empty:
        return dash.no_update, dash.no_update, dash.no_update

    # ✅ Reconstruir tabla si existe
    if existing_data and len(existing_data) > 0:
        df_table = pd.DataFrame(existing_data).set_index("Model")
    else:
        df_table = pd.DataFrame()

     # Loop sobre cada par de modelos seleccionados (incluyendo base)
    all_models = [model_data_selected["model_name"]] + models_selected

    for i, model_i in enumerate(all_models):
        name_file_i = model_information.get_configuration_by_model_name(model_i)['model_description']['config_files']['model_file']
        pred_i = generate_prediction_name(name_file_i)

        for j, model_j in enumerate(all_models):
            if i >= j:  # evitar duplicados y diagonal (se llenan simétricamente)
                continue

            name_file_j = model_information.get_configuration_by_model_name(model_j)['model_description']['config_files']['model_file']
            pred_j = generate_prediction_name(name_file_j)

            # Validar columnas
            if pred_i not in df_window.columns or pred_j not in df_window.columns:
                continue

            # Datos válidos
            df_valid = pd.DataFrame({"y_true": df_window[pred_i], "y_pred": df_window[pred_j]}).dropna()
            if df_valid.empty:
                continue

            # Calcular métrica
            result = compute_metric(metric_selected, df_valid["y_true"], df_valid["y_pred"])
            result = round(result, 4)

            # Crear tabla si está vacía
            if df_table.empty:
                df_table = pd.DataFrame()

            # Asegurar filas/columnas
            for m in [model_i, model_j]:
                if m not in df_table.columns:
                    df_table[m] = None
                if m not in df_table.index:
                    new_row = {col: None for col in df_table.columns}
                    df_table.loc[m] = new_row

            # Diagonal como NaN
            for m in df_table.index:
                df_table.loc[m, m] = "NaN"

            # Guardar métrica en posiciones simétricas
            df_table.loc[model_i, model_j] = result
            df_table.loc[model_j, model_i] = result

    # Reset index para DataTable
    if not df_table.empty:
        base_name = model_data_selected["model_name"]  # ✅ siempre el modelo base en (0,0)
        df_table, columns = reorder_dataframe_for_table(df_table,model_data_selected)
        # Estilo dinámico: poner en negrita la fila del modelo base
        style_data_conditional = [
            {
                "if": {"filter_query": f'{{Model}} = "{base_name}"'},
                "fontWeight": "bold"
            }
        ]
        return df_table.to_dict("records"), columns, style_data_conditional

    return dash.no_update, dash.no_update, dash.no_update


@dash.callback(
    Output("time-ws-slider-labels", "children"),
    Output("time-window-size", "max"),
    Input("store-selected-state", "data"),
    Input("time-window-size", "value")
)
def update_window_size_slider_labels(data, slider_range):
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
        print("No experiment ID Selected")
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

        return [f"Last {n_total} elements - Selected {n_selected}",
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

