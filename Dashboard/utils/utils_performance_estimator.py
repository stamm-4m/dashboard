import re
import plotly.express as px
import numpy as np

def generate_prediction_name(model_file):
    # Regular expression to extract the text between the last two underscores '_'
    match = re.search(r'_([^_]*)\.pkl$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .pkl
        return f"{model_type}_penicillin_prediction"
    
    match = re.search(r'_([^_]*)\.keras$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .keras
        return f"{model_type}_penicillin_prediction"
    
    match = re.search(r'_([^_]*)\.rds$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .rds
        return f"{model_type}_penicillin_prediction"
    
    return "penicillin_prediction"


color_palette = px.colors.qualitative.Dark24
color_index = 0  # Global index to select colors from the list

def get_next_color():
    """ Retrieves a different color each time it is called """
    global color_index
    color = color_palette[color_index % len(color_palette)]  # Loops if colors run out
    color_index += 1  # Advances the index for the next line
    return color

# Point-by-point metric functions
def calculate_mae(y_true, y_pred):
    return abs(y_true - y_pred)  # Point-by-point MAE

def calculate_mse(y_true, y_pred):
    return (y_true - y_pred) ** 2  # Point-by-point MSE

def calculate_rmse(y_true, y_pred):
    return np.sqrt((y_true - y_pred) ** 2)  # Point-by-point RMSE

def calculate_vpd(y_true, y_pred):
    return np.abs((y_pred - y_true) / y_true)  # Point-by-point VPD

# Metric functions that return a single value
def calculate_pcc(y_true, y_pred):
    return np.corrcoef(y_true, y_pred)[0, 1]  # Single value

def calculate_cossim(y_true, y_pred):
    return np.dot(y_true, y_pred) / (np.linalg.norm(y_true) * np.linalg.norm(y_pred))  # Single value

def calculate_cv(y_true, y_pred):
    return np.std(y_pred) / np.mean(y_pred)  # Single value
