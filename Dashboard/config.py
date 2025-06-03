import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_env_var(var_name):
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        raise ValueError(f"The environment variable '{var_name}' is not defined or is empty.")
    return value

# InfluxDB connection variables (required)
INFLUXDB_URL = check_env_var("INFLUXDB_URL")
INFLUXDB_TOKEN = check_env_var("INFLUXDB_TOKEN")
INFLUXDB_ORG = check_env_var("INFLUXDB_ORG")
INFLUXDB_BUCKET = check_env_var("INFLUXDB_BUCKET")


BACH_ID = os.getenv("BACH_ID")
DB_SQLITE_DIR = os.getenv("DB_SQLITE_DIR")

# Local InfluxDB connection variables (optional, but you can validate them if needed)
INFLUXDB_URL_LOCAL = os.getenv("INFLUXDB_URL_LOCAL")
INFLUXDB_TOKEN_LOCAL = os.getenv("INFLUXDB_TOKEN_LOCAL")
INFLUXDB_ORG_LOCAL = os.getenv("INFLUXDB_ORG_LOCAL")
INFLUXDB_BUCKET_LOCAL = os.getenv("INFLUXDB_BUCKET_LOCAL")

BASE_URL_API = os.getenv("BASE_URL_API")
