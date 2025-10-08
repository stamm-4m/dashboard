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

logger = logging.getLogger(__name__)

import numpy as np
import pandas as pd

def generate_predictions(batch_id, n=None):
    """
    Returns a new fake row based on the last real row in the batch data.
    Adds small random variations to numeric columns and updates the timestamp.
    Also generates random values for prediction columns if they exist.
    """
    dfc = influxdb_handler.get_data_until_latest(batch_id)
    if dfc.empty:
        return None

    # Tomar la última fila real
    last_row = dfc.iloc[-1].copy()

    # Crear nueva fila basada en la última
    new_row = last_row.copy()

    # Aplicar pequeñas variaciones aleatorias a columnas numéricas
    for col in dfc.select_dtypes(include=[np.number]).columns:
        new_row[col] = new_row[col] + np.random.normal(0, 0.01 * new_row[col])

    # Columnas de predicción
    pred_cols = [
        'pred_penicillin_CART',
        'pred_penicillin_GBM',
        'pred_penicillin_LSTM',
        'pred_penicillin_SVM'
    ]
    
    for col in pred_cols:
        if col in new_row:
            # Generar valor aleatorio positivo similar a la concentración
            new_row[col] = np.random.uniform(0, 50)

    # Actualizar timestamp al momento actual si existe columna '_time'
    if '_time' in new_row:
        new_row['_time'] = pd.Timestamp.now()

    return new_row

# n is step current
""" def generate_predictions(batch_id, n):
    dfc = influxdb_handler.get_data_until_latest(batch_id)
    if n > len(dfc):
        return None  # o una señal para no actualizar más
    return dfc.iloc[n]
 """
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
def generate_prediction_name(model_file):
    # Regular expression to extract the text between the last two underscores '_'
    match = re.search(r'_([^_]*)\.pkl$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .pkl
        return f"pred_penicillin_{model_type}"
    
    match = re.search(r'_([^_]*)\.keras$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .keras
        return f"pred_penicillin_{model_type}"
    
    match = re.search(r'_([^_]*)\.rds$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .rds
        return f"pred_penicillin_{model_type}"
    
    return "penicillin_concentration"

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
    Initialize data_prediction dictionary with all existing values in dfc.
    This includes times, predictions, and selected variables.
    """
    # Convert all times
    times = dfc["_time"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    data_prediction = {"_time": times}

    # Predictions
    if name_prediction in dfc:
        data_prediction[name_prediction] = dfc[name_prediction].tolist()
    else:
        data_prediction[name_prediction] = []

    # Variables
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
    tiempo_pred = pd.to_datetime(predicted_values['_time'])
    nivel_pred = predicted_values.get(name_prediction, None)

    logger.info(f"Updating prediction: {tiempo_pred}, {nivel_pred}")

    # ⏱️ Agregar timestamp
    data_prediction["_time"].append(tiempo_pred.strftime("%Y-%m-%d %H:%M:%S"))

    # 🔮 Agregar valor de predicción
    if name_prediction not in data_prediction:
        data_prediction[name_prediction] = []
    data_prediction[name_prediction].append(nivel_pred)

    # 📊 Variables seleccionadas
    for variable in selected_variables:
        var_name = variable["variable_name"]
        if var_name == name_prediction:
            continue

        value_variable = predicted_values.get(var_name)

        if value_variable is None:
            # 🚨 Si no existe, lanzar toast y mantener alineación
            if var_name not in data_prediction:
                data_prediction[var_name] = []
            data_prediction[var_name].append(None)
            create_toast(f"Warning: The variable '{var_name}' is not part of the model.")
        else:
            if var_name not in data_prediction:
                data_prediction[var_name] = []
            # Guardar valor o None si es NaN → mantiene sincronía
            data_prediction[var_name].append(value_variable if not pd.isna(value_variable) else None)

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
    Construye la figura con todas las trazas (predicción + variables seleccionadas)
    y aplica layout dinámico con ejes de colores.
    """
    fig = go.Figure()

    # Diccionario de colores incluyendo siempre la predicción
    color_map = {var["variable_name"]: color for var, color in zip(selected_variables, px.colors.qualitative.Dark24)}
    color_map[name_prediction] = 'black'  # Color fijo para la predicción

    # Agregar línea de predicción
    if name_prediction in data_prediction:
        fig.add_trace(go.Scatter(
            x=data_prediction["_time"], 
            y=data_prediction[name_prediction], 
            mode="lines",
            name=name_prediction.capitalize(),
            yaxis=y_axes[name_prediction],
            line=dict(color=color_map[name_prediction], dash="dash")  # Estilo predicción
        ))

    # Agregar líneas de las variables seleccionadas
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

    # Configuración dinámica de ejes
    trace_colors = {axis: color_map[var] for var, axis in y_axes.items() if var in color_map}

    layout_yaxes = {}
    for i, (axis, color) in enumerate(trace_colors.items(), start=1):
        layout_yaxes[axis] = {
            'title': y_axis_labels[axis],
            'title_font': dict(color=color),
            'side': 'left' if i == 1 else 'right',
            'position': 1 - (0.10 * (i - 2)) if i > 1 else None,
            'overlaying': 'y' if i > 1 else None,
            'tickfont': dict(color=color)
        }

    layout_update = {f'yaxis{i}': layout_yaxes.get(f'y{i}', {}) for i in range(1, len(y_axes) + 1)}

    # Configurar layout final
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
    fig.update_layout(xaxis=dict(rangeselector=dict(
        buttons=[
            dict(count=6, label="6 hours", step="hour", stepmode="backward"),
            dict(count=1, label="1 day", step="day", stepmode="backward"),
            dict(count=1, label="1 month", step="month", stepmode="backward"),
            dict(step="all")
        ]),
        type="date"
    ))

    return fig

