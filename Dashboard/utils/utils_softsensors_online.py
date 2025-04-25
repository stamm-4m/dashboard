import dash_bootstrap_components as dbc
import requests
import json
from Dashboard.InfluxDb import influxdb_handler  # Retrieve the created instance


def generate_predictions(batch_id, datamodel, n):
    dfc = influxdb_handler.get_data_by_batch_id2(batch_id)
    
    # Extract model features
    #str_features = [feature["name"] for feature in datamodel["features"]]
    # print("str_features", str_features)
    
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
        return df_predicted

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
