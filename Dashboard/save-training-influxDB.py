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
data = data[data["experiment_ID"] == 99]

# Start timestamp: **Current time**
start_timestamp = int(time.time())  # Get current time in seconds
start_timestamp_ns = start_timestamp * 1_000_000_000  # Convert to nanoseconds

# Prepare and write data to InfluxDB
batch_size = 5000  # Adjust batch size if needed
points = []



# Loop through the rows of the data to store results
for idx, row in data.iterrows():
    experiment_id = str(row["experiment_ID"])

    # Calculate timestamp for each point (+5 seconds per point)
    timestamp = int(row["experiment_time"]) if pd.notna(row["experiment_time"]) else int(time.time())
    timestamp_ns = start_timestamp_ns + (timestamp * 1_000_000_000)


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
