import re
import plotly.express as px
import numpy as np

def generate_prediction_name(model_file):
    # Expresión regular para extraer el texto entre los dos últimos guiones bajos '_'
    match = re.search(r'_([^_]*)\.pkl$', model_file)
    
    if match:
        model_type = match.group(1)  # Extrae la parte antes de .pkl
        return f"{model_type}_penicillin_prediction"
    
    match = re.search(r'_([^_]*)\.keras$', model_file)
    
    if match:
        model_type = match.group(1)  # Extrae la parte antes de .keras
        return f"{model_type}_penicillin_prediction"
    
    match = re.search(r'_([^_]*)\.rds$', model_file)
    
    if match:
        model_type = match.group(1)  # Extrae la parte antes de .rds
        return f"{model_type}_penicillin_prediction"
    
    return "penicilin_prediction"


color_palette = px.colors.qualitative.Dark24
color_index = 0  # Índice global para seleccionar colores de la lista

def get_next_color():
    """ Obtiene un color diferente cada vez que se llama """
    global color_index
    color = color_palette[color_index % len(color_palette)]  # Cicla si se acaban los colores
    color_index += 1  # Avanza el índice para la siguiente línea
    return color
#  Funciones de métricas punto por punto
def calculate_mae(y_true, y_pred):
    return abs(y_true - y_pred)  # MAE punto a punto

def calculate_mse(y_true, y_pred):
    return (y_true - y_pred) ** 2  # MSE punto a punto

def calculate_rmse(y_true, y_pred):
    return np.sqrt((y_true - y_pred) ** 2)  # RMSE punto a punto

def calculate_vpd(y_true, y_pred):
    return np.abs((y_pred - y_true) / y_true)  # VPD punto a punto

#  Funciones de métricas que devuelven un solo valor
def calculate_pcc(y_true, y_pred):
    return np.corrcoef(y_true, y_pred)[0, 1]  # Valor único

def calculate_cossim(y_true, y_pred):
    return np.dot(y_true, y_pred) / (np.linalg.norm(y_true) * np.linalg.norm(y_pred))  # Valor único

def calculate_cv(y_true, y_pred):
    return np.std(y_pred) / np.mean(y_pred)  # Valor único

