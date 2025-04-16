import os
from dotenv import load_dotenv

# load variables from file .env
load_dotenv()

# Variables of conection to InfluxDB
INFLUXDB_URL = os.getenv("INFLUXDB_URL")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")
BACH_ID = os.getenv("BACH_ID") 
# Variables of conection Local to InfluxDB
INFLUXDB_URL_LOCAL = os.getenv("INFLUXDB_URL_LOCAL")
INFLUXDB_TOKEN_LOCAL = os.getenv("INFLUXDB_TOKEN_LOCAL")
INFLUXDB_ORG_LOCAL = os.getenv("INFLUXDB_ORG_LOCAL")
INFLUXDB_BUCKET_LOCAL = os.getenv("INFLUXDB_BUCKET_LOCAL")