import dash_bootstrap_components as dbc
import requests
import json
import re
from utils import model_information
from InfluxDb import influxdb_handler  # Retrieve the created instance


# Calls the function again to read  'Models
def reload_models():
    model_information.configurations = []
    model_information.load_all_models()

def generate_predictions(batch_id, datamodel, n):
    dfc = influxdb_handler.get_data_by_batch_id2(batch_id)

    dfc = dfc.dropna()

    return dfc

def create_toast(message):
    return dbc.Toast(
        message,
        id="toast",
        header="Notification",
        icon="primary",  # You can change this to "danger", "success", etc.
        duration=4000,  # Displays for 4 seconds
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
