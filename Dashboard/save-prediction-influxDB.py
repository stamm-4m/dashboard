# -*- coding: utf-8 -*-
"""
Created on Tue Mar  4 08:57:40 2025

@author: David Camilo Corrales
"""
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from tensorflow.keras.models import load_model
import pandas as pd
import datetime
import joblib 

token = "jJfKhzqC-M9nbmslXlCzOVsCsLy1TMcNQFnP2s0CS-5gb7hcLZIfn3CIEo3lmwXbyZWU6s5lKEv9KQUcXZA1JQ=="
org = "INRAE"
url = "http://147.100.164.27:8080"
bucket = "STAMM_DATA"
#data_path = "C:/Users/corrales/Documents/IndPenSim/Soft sensor construction/data/"

#url="http://localhost:8086"
#org="unicauca"
#token="_X62mF4Azxzaook3JDz2loWNTXaJvgJ4tI4UQVXSdrpzM2BogEPmgWLz_T9sv61NxITxVYkNd7BOvxuwNlcixA=="
#bucket="STAMM_BUCKET"
#data_path="experiment_ID"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Load metadata for column mapping
#metadata = pd.read_csv(data_path + "Penicillin_Metadata.csv")
metadata = pd.read_csv("Data/Penicillin_Metadata.csv")
column_map = dict(zip(metadata["Variable_name"], metadata["Variable_name_InfluxDB"]))
allowed_columns = list(metadata["Variable_name_InfluxDB"])  # Only keep these columns

# Load main data
#data = pd.read_csv(data_path + "100_Batches_IndPenSim_V3.1.csv")
data = pd.read_csv('Data/100_Batches_IndPenSim_V3.1.csv')

# Replace column names based on metadata
data.rename(columns=column_map, inplace=True)

# Keep only columns listed in `Variable_name_InfluxDB`
data = data[[col for col in data.columns if col in allowed_columns or col in ["experiment_ID", "experiment_time"]]]

# Filter data for Experiment 1 only
data = data[data["experiment_ID"] == 91]

# Start timestamp: **Current time**
start_timestamp = int(time.time())  # Get current time in seconds
start_timestamp_ns = start_timestamp * 1_000_000_000  # Convert to nanoseconds

# Prepare and write data to InfluxDB
batch_size = 5000  # Adjust batch size if needed
points = []

# Load CART model, Random Forest model, and SVM models
#model_CART = joblib.load("C:/Users/corrales/Documents/IndPenSim/Soft sensor construction/Models/0005_[Python]_penicillin_CART.pkl")
model_CART = joblib.load("../ML_Repository/0005_[Python]_penicillin_CART.pkl")
#model_RF = joblib.load("C:/Users/corrales/Documents/IndPenSim/Soft sensor construction/Models/0001_[python]_penicillin_RF.pkl")
model_RF = joblib.load('../ML_Repository/0001_[python]_penicillin_RF.pkl')
#model_SVM = joblib.load("C:/Users/corrales/Documents/IndPenSim/Soft sensor construction/Models/0007_[python]_penicillin_SVM.pkl")
model_SVM = joblib.load("../ML_Repository/0007_[python]_penicillin_SVM.pkl")

model_GBM = joblib.load("../ML_Repository/0008_[Python]_penicillin_GBM.pkl")

features_scaler_SVM = model_SVM["feature_scaler"]
target_scaler_SVM   = model_SVM["target_scaler"]
model_SVM = model_SVM["model"]

# Load the LSTM model and scalers
#model_LSTM = load_model("C:/Users/corrales/Documents/IndPenSim/Soft sensor construction/Models/0009_[Python]_penicillin_LSTM.keras")
model_LSTM = load_model("../ML_Repository/0009_[Python]_penicillin_LSTM.keras")
features_scaler_LSTM = joblib.load("../ML_Repository/0009_[Python]_penicillin_LSTM_features_scaler.pkl")
target_scaler_LSTM = joblib.load("../ML_Repository/0009_[Python]_penicillin_LSTM_target_scaler.pkl")


# Loop through the rows of the data to store results
for idx, row in data.iterrows():
    experiment_id = str(row["experiment_ID"])

    # Calculate timestamp for each point (+5 seconds per point)
    timestamp = int(row["experiment_time"]) if pd.notna(row["experiment_time"]) else int(time.time())
    timestamp_ns = start_timestamp_ns + (timestamp * 1_000_000_000)

    ########## ------------> CART <------------ ##########    
    inputs = row[['temperature', 'pH','dissolved_oxygen_concentration',
                  'agitator','CO2_percent_in_off_gas', 'oxygen_in_percent_in_off_gas', 
                  'vessel_volume', 'sugar_feed_rate']].to_frame().T
    prediction_CART = model_CART.predict(inputs)
    prediction_CART = prediction_CART.item()

    ########## ------------> RF <------------ ##########
    prediction_RF = model_RF.predict(inputs)
    prediction_RF = prediction_RF.item()

    ########## ------------> SVM <------------ ##########
    # Scale the features using the feature scaler
    inputs_scaled = features_scaler_SVM.transform(inputs)

    # Make SVM prediction
    prediction_SVM_scaled = model_SVM.predict(inputs_scaled)
    # Inverse scale the prediction to get original scale
    prediction_SVM = target_scaler_SVM.inverse_transform(prediction_SVM_scaled.reshape(-1, 1)).ravel().item()

    # Debugging SVM prediction
    print("SVM Prediction:", prediction_SVM)

    ########## ------------> GBM  <------------ ##########

    prediction_GBM = model_GBM.predict(inputs)
    prediction_GBM = prediction_GBM.item()

    ########## ------------> LSTM  <------------ ##########

    # Scale the input features using the scaler
    inputs_scaled = features_scaler_LSTM.transform(inputs)
    inputs_scaled = inputs_scaled.reshape((inputs_scaled.shape[0], 1, inputs_scaled.shape[1]))

    # Make the prediction using the LSTM model
    prediction_LSTM_scaled = model_LSTM.predict(inputs_scaled)

    # Inverse scale the prediction to get the original scale
    prediction_LSTM = target_scaler_LSTM.inverse_transform(prediction_LSTM_scaled).item()


    # Store other data points in InfluxDB
    for column in data.columns:
        if column not in ["experiment_ID", "experiment_time"]:
            value = row[column]
            if pd.notna(value):  # Avoid NaN values
                point = (
                    Point(experiment_id)
                    .field(column, float(value))
                    .time(timestamp_ns, WritePrecision.NS)  # Use calculated timestamp
                )
                points.append(point)

    ################# Loading ML soft sensors ############################        
    # Writing CART point
    CART_point = (
         Point(experiment_id)
             .field("CART_penicillin_prediction", float(prediction_CART)) 
             .time(timestamp_ns, WritePrecision.NS)  # Use calculated timestamp
    )
    print("CART Point:", CART_point.to_line_protocol())  # Debugging output
    write_api.write(bucket=bucket, org=org, record=[CART_point])  # Write to InfluxDB immediately
    
    # Writing RF point
    RF_point = (
         Point(experiment_id)
             .field("RF_penicillin_prediction", float(prediction_RF)) 
             .time(timestamp_ns, WritePrecision.NS)  # Use calculated timestamp
    )
    print("RF Point:", RF_point.to_line_protocol())  # Debugging output
    write_api.write(bucket=bucket, org=org, record=[RF_point])  # Write to InfluxDB immediately
    
    # Writing SVM point
    SVM_point = (
         Point(experiment_id)
             .field("SVM_penicillin_prediction", float(prediction_SVM)) 
             .time(timestamp_ns, WritePrecision.NS)  # Use calculated timestamp
    )
    print("SVM Point:", SVM_point.to_line_protocol())  # Debugging output
    write_api.write(bucket=bucket, org=org, record=[SVM_point])  # Write to InfluxDB immediately

    # Writing GBM point
    GBM_point = (
         Point(experiment_id)
             .field("GBM_penicillin_prediction", float(prediction_GBM)) 
             .time(timestamp_ns, WritePrecision.NS)  # Use calculated timestamp
    )
    print("GBM Point:", GBM_point.to_line_protocol())  # Debugging output
    write_api.write(bucket=bucket, org=org, record=[GBM_point])  # Write to InfluxDB immediately
    
    # Writing LSTM point
    LSTM_point = (
        Point(experiment_id)
            .field("LSTM_penicillin_prediction", float(prediction_LSTM)) 
            .time(timestamp_ns, WritePrecision.NS)  # Use calculated timestamp
    )

    # Append to the points list to ensure it still works with batch writing
    points.append(CART_point)
    points.append(RF_point)
    points.append(SVM_point)
    points.append(GBM_point)
    points.append(LSTM_point)
    ########## ------------> SVM <------------ ##########    

    # Write in batches for efficiency
    if len(points) >= batch_size:
        write_api.write(bucket=bucket, org=org, record=points)
        points.clear()

# Write any remaining points
if points:
    write_api.write(bucket=bucket, org=org, record=points)
    points.clear()    
else:
    print("No points prepared for writing!")

print("Data insertion completed successfully every 5 seconds for Experiment 1!")
