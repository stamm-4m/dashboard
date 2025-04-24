import dash_bootstrap_components as dbc
import requests
import json
import re
from utils import model_information
from InfluxDb import influxdb_handler  # Retrieve the created instance


# Calls the function again to read YAML files from the 'Models' folder
def reload_models_yaml():
    model_information.configurations = []
    model_information.load_all_models()

def generate_predictions(batch_id, datamodel, n):
    dfc = influxdb_handler.get_data_by_batch_id2(batch_id)

    # Extract model features
    #str_features = [feature["name"] for feature in datamodel["features"]]
    # print("str_datamodel", datamodel)
    
    # Model language
    language = datamodel["language"]
    for feature in datamodel["features"]:
        # Model lag for the features
        lag = 0#feature["lag"]
    
    if language == "R":
        # Example data that matches your model's expected input format
        example_data = {
            "temperature": 298.22,
            "pH": 6.4472,
            "dissolved_oxygen_concentration": 30,
            "agitator": 100,
            "CO2_percent_in_off_gas": 0.089514,
            "oxygen_in_percent_in_off_gas": 0.19595,
            "vessel_volume": 58479,
            "sugar_feed_rate": 8
            # Add more features as per your model's input requirements
        }

        # Convert the example data to JSON
        example_json = json.dumps(example_data)
        ######################################### Random Forest ######################################### 
        # Make a POST request to the API
        response = requests.post(
            url="http://localhost:8000/rf/0002_penicillin_RF",  # API endpoint
            data=example_json,                                   # Send the JSON data
            headers={"Content-Type": "application/json"}        # Specify that the body is JSON
        )
        # Check the response
        print(response.json())  # This will print the response in JSON format        
        ######################################### CUBIST #################################################
        # Make a POST request to the API
        response = requests.post(
            url="http://localhost:8000/cubist/0003_penicillin_CUBIST",  # API endpoint
            data=example_json,                                   # Send the JSON data
            headers={"Content-Type": "application/json"}        # Specify that the body is JSON
        )

        # Check the response
        print(response.json())  
    
    # Verify that input features do not have an input window
    if lag == 0:
        if n < len(dfc):  # Verify that n is still valid after filtering
            df_predicted = dfc.iloc[n]
        else:
            df_predicted = None  # Or handle the case where n is no longer valid
            
        return dfc

    return df_predicted

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
