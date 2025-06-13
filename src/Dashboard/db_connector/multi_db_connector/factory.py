"""
Created on Wed May 14 10:05:17 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr

"""

from .influxdb_connector import InfluxDBConnector
from .postgres_connector import PostgresConnector

def get_connector(config):
    db_type = config["type"]
    if db_type == "influxdb":
        return InfluxDBConnector(config)
    elif db_type == "postgres":
        return PostgresConnector(config)
    else:
        raise ValueError(f"Unsupported DB type: {db_type}")