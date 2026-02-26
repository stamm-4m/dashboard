import dash_bootstrap_components as dbc
import requests
import json
from Dashboard.InfluxDb import influxdb_handler  # Retrieve the created instance
import re
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import logging
import pandas as pd
from Dashboard.utils.utils_model_information import get_model_information  # Retrieve the created instance


logger = logging.getLogger(__name__)

import numpy as np
import pandas as pd

def reload_models(project_id): 
    model_information = get_model_information(project_id)
    model_information.configurations = []
    model_information.load_all_models()

def get_latest_index(experiment_id: str) -> int:
    """
    Get the latest row index available for a given experiment.
    This is used to start predictions from the current point forward.
    """
    try:
        dfc = influxdb_handler.get_data_until_latest(experiment_id)
        if dfc is None or dfc.empty:
            print(f"⚠️ No data found for experiment {experiment_id}. Starting from 0.")
            return 0
        
        # Retornar el último índice entero (número de filas - 1)
        return len(dfc) - 1

    except Exception as e:
        print(f"⚠️ Error retrieving latest index for {experiment_id}: {e}")
        return 0

def create_toast(message,seg = 4000):
    return dbc.Toast(
        message,
        id="toast",
        header="Notification",
        icon="primary",  # You can change this to "danger", "success", etc.
        duration=seg,  # Displays for 4 seconds
        is_open=True,
        dismissable=True,
        style={"position": "fixed", "top": 10, "right": 10, "zIndex": 1000},
    )

def build_figure_from_data(data_prediction, selected_variables, name_prediction):
    fig = go.Figure()
    logger.info(f'data_prediction: {data_prediction}')
    if data_prediction is None or "_time" not in data_prediction:
        return fig

    # Colores
    color_map = {var["variable_name"]: color for var, color in zip(selected_variables, px.colors.qualitative.Dark24)}
    color_map[name_prediction] = 'black'

    # Agregar predicciones si existen
    if name_prediction in data_prediction:
        fig.add_trace(go.Scatter(
            x=data_prediction["_time"],
            y=data_prediction[name_prediction],
            mode="lines",
            name=name_prediction.capitalize(),
            line=dict(color=color_map[name_prediction], dash="dash")
        ))

    # Agregar variables seleccionadas
    for var in selected_variables:
        var_name = var["variable_name"]
        if var_name in data_prediction:
            fig.add_trace(go.Scatter(
                x=data_prediction["_time"],
                y=data_prediction[var_name],
                mode="lines",
                name=var_name.capitalize(),
                line=dict(color=color_map.get(var_name, "gray"))
            ))

    fig.update_layout(
        title="Performance Penicillin",
        xaxis_title="Time",
        yaxis_title="Values",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def init_data_prediction(dfc, selected_variables, name_prediction):
    """
    Initializes the data_prediction dictionary with all existing values in the DataFrame.

    Includes timestamps, predictions, and selected variables for the plot.

    Args:
        dfc (pd.DataFrame): DataFrame containing time-series data.
        selected_variables (list): List of selected variable dictionaries (each containing "variable_name").
        name_prediction (str): Column name of the prediction values.

    Returns:
        dict: Dictionary with "_time", prediction values, and selected variable data.
    """
    # Convert all timestamps to string format for serialization
    times = dfc["_time"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    data_prediction = {"_time": times}

    # Add prediction values
    if name_prediction in dfc:
        data_prediction[name_prediction] = dfc[name_prediction].tolist()
    else:
        data_prediction[name_prediction] = []

    # Add all selected variable values
    for v in selected_variables:
        var_name = v["variable_name"]
        if var_name in dfc:
            data_prediction[var_name] = dfc[var_name].tolist()
        else:
            data_prediction[var_name] = []

    return data_prediction

def append_prediction(data_prediction, predicted_values, name_prediction, selected_variables):
    """
    Append new prediction and variable values to data_prediction.
    Keep alignment across variables and prediction.
    Show toast if a variable is missing in predicted_values.
    """
    # --- Asegurar que predicted_values sea un diccionario simple ---
    if isinstance(predicted_values, pd.DataFrame):
        predicted_values = predicted_values.iloc[0].to_dict()
    elif isinstance(predicted_values, pd.Series):
        predicted_values = predicted_values.to_dict()

    # Obtener tiempo y valor de predicción
    tiempo_pred = pd.to_datetime(predicted_values.get('_time'))
    nivel_pred = predicted_values.get(name_prediction)

    logger.info(f"Updating prediction: {tiempo_pred}, {nivel_pred}")

    # Si no hay tiempo, abortar (evita índices rotos)
    if tiempo_pred is None:
        logger.warning("Predicted value has no '_time' field, skipping append.")
        return data_prediction

    # --- Asegurar estructura de data_prediction ---
    if "_time" not in data_prediction:
        data_prediction["_time"] = []
    data_prediction["_time"].append(tiempo_pred)

    # 🔮 Agregar valor de predicción
    if name_prediction not in data_prediction:
        data_prediction[name_prediction] = []
    data_prediction[name_prediction].append(
        nivel_pred if not pd.isna(nivel_pred) else None
    )

    # 📊 Agregar las variables seleccionadas
    for variable in selected_variables:
        var_name = variable["variable_name"]
        if var_name == name_prediction:
            continue

        # Obtener valor de la variable
        value_variable = predicted_values.get(var_name, None)

        # Inicializar si no existe
        if var_name not in data_prediction:
            data_prediction[var_name] = []

        # Si falta el valor, mostrar advertencia y mantener alineación
        if value_variable is None or pd.isna(value_variable):
            data_prediction[var_name].append(None)
            logger.warning(f"⚠️ Variable '{var_name}' missing in prediction row.")
        else:
            data_prediction[var_name].append(value_variable)

    return data_prediction


def update_axes_labels(data_prediction, selected_variables, name_prediction):
    """
    Devuelve y_axes y y_axis_labels basados en las variables existentes en data_prediction.
    """
    y_axes = {}
    y_axis_labels = {}
    i = 1
    for var in selected_variables:
        var_name = var["variable_name"]
        if var_name in data_prediction:
            axis = f"y{i}"
            y_axes[var_name] = axis
            y_axis_labels[axis] = var_name.capitalize()
            i += 1

    # Asegurarse de incluir la predicción
    if name_prediction in data_prediction and name_prediction not in y_axes:
        axis = f"y{i}"
        y_axes[name_prediction] = axis
        y_axis_labels[axis] = name_prediction.capitalize()

    return y_axes, y_axis_labels

def build_figure_with_traces(data_prediction, selected_variables, name_prediction, y_axes, y_axis_labels):
    """
    Builds a Plotly figure with all traces (prediction + selected variables) 
    and applies a dynamic layout with multiple colored axes.

    Args:
        data_prediction (dict): Dictionary containing time, prediction, and variable data.
        selected_variables (list): List of selected variable dictionaries (each containing "variable_name").
        name_prediction (str): Column name of the prediction values.
        y_axes (dict): Dictionary mapping variable names to y-axis identifiers.
        y_axis_labels (dict): Dictionary mapping y-axis identifiers to axis labels.

    Returns:
        go.Figure: Configured Plotly figure with traces and layout.
    """
    fig = go.Figure()

    # Color dictionary including prediction line
    color_map = {var["variable_name"]: color for var, color in zip(selected_variables, px.colors.qualitative.Dark24)}
    color_map[name_prediction] = 'black'  # Fixed color for prediction line

    # Add prediction line
    if name_prediction in data_prediction:
        fig.add_trace(go.Scatter(
            x=data_prediction["_time"],
            y=data_prediction[name_prediction],
            mode="lines",
            name=name_prediction.capitalize(),
            yaxis=y_axes.get(name_prediction, "y1"),
            line=dict(color=color_map[name_prediction], dash="dash")  # Dashed style for prediction
        ))
    #logger.debug(f"data_prediction: \n {data_prediction}")
    # Add traces for each selected variable
    for var in selected_variables:
        var_name = var["variable_name"]
        if var_name in data_prediction:
            if var_name not in y_axes:
                y_axes[var_name] = f"y{len(y_axes) + 1}"
                y_axis_labels[y_axes[var_name]] = var_name.capitalize()

            fig.add_trace(go.Scatter(
                x=data_prediction["_time"],
                y=data_prediction[var_name],
                mode="lines",
                name=var_name.capitalize(),
                yaxis=y_axes[var_name],
                line=dict(color=color_map[var_name])
            ))

    # Configure dynamic axis colors
    trace_colors = {axis: color_map[var] for var, axis in y_axes.items() if var in color_map}

    layout_yaxes = {}
    for i, (axis, color) in enumerate(trace_colors.items(), start=1):
        layout_yaxes[axis] = {
            'title': y_axis_labels[axis],
            'title_font': dict(color=color),
            'side': 'left' if i == 1 else 'right',
            #'position': 1 - (1.10 * (i - 2)) if i > 1 else None,
            'overlaying': 'y' if i > 1 else None,
            'tickfont': dict(color=color)
        }
          # Keep your logic, but ensure valid positions
        if i == 1:
            layout_yaxes[axis]['position'] = None

        elif i == 2:
            layout_yaxes[axis]['position'] = 1   # second axis at right edge

        else:
            layout_yaxes[axis]['position'] = 1
            layout_yaxes[axis]['anchor'] = 'free'
            # push the title and ticks further out progressively (pixels)
            layout_yaxes[axis]['title_standoff'] = 30 * (i - 1)
            layout_yaxes[axis]['ticklabelposition'] = 'outside'
            layout_yaxes[axis]['ticklabeloffset'] = 20 * (i - 1)
            layout_yaxes[axis]['ticklen'] = 6
            layout_yaxes[axis]['automargin'] = True

    layout_update = {f'yaxis{i}': layout_yaxes.get(f'y{i}', {}) for i in range(1, len(y_axes) + 1)}

    # Final layout configuration
    fig.update_layout(
        title="Performance Penicillin",
        xaxis_title="Time",
        yaxis_title="Penicillin",
        xaxis=dict(tickangle=-45),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
        **layout_update
    )

    # Add range selector for time
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=6, label="6 hours", step="hour", stepmode="backward"),
                    dict(count=1, label="1 day", step="day", stepmode="backward"),
                    dict(count=1, label="1 month", step="month", stepmode="backward"),
                    dict(step="all")
                ]
            ),
            type="date"
        )
    )
    fig.update_layout(margin=dict(r=200))
    return fig

def update_xaxis_range(fig, relayout_data, data_prediction):
    """
    Update x-axis range dynamically:
    - Keep user zoom if new data is within range.
    - Auto-scroll if new data arrives outside the current range.

    Parameters
    ----------
    fig : plotly.graph_objs.Figure
        The figure to update.
    relayout_data : dict or None
        Data from Plotly's relayoutData event (contains zoom/pan range).
    data_prediction : pandas.DataFrame or dict
        Object containing "_time" values (can be list or Series).

    Returns
    -------
    fig : plotly.graph_objs.Figure
        Updated figure.
    """
    import pandas as pd

    # 🔹 Obtener último tiempo de data_prediction
    if "_time" not in data_prediction or len(data_prediction["_time"]) == 0:
        fig.update_xaxes(autorange=True)
        return fig

    time_values = data_prediction["_time"]
    latest_time = pd.to_datetime(time_values[-1] if isinstance(time_values, list) else time_values.iloc[-1])

    # 🔹 Si hay un rango actual del usuario (zoom/pan)
    if relayout_data and 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
        start_range = pd.to_datetime(relayout_data['xaxis.range[0]'])
        end_range = pd.to_datetime(relayout_data['xaxis.range[1]'])
        delta = end_range - start_range

        # Si el nuevo punto está fuera del rango → mover la ventana
        if latest_time > end_range:
            new_start = latest_time - delta
            new_end = latest_time
            fig.update_xaxes(range=[new_start, new_end])
        else:
            # Mantener zoom actual
            fig.update_xaxes(range=[start_range, end_range])
    else:
        # 🔹 Si no hay zoom previo, usar autoescala (modo seguimiento automático)
        fig.update_xaxes(autorange=True)

    return fig
