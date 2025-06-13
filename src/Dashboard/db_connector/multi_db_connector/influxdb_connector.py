"""
Created on Wed May 14 10:15:10 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr

"""

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
from .base import BaseDBConnector
import pandas as pd


class InfluxDBConnector(BaseDBConnector):
    def __init__(self, url, token, org, bucket):
        if not all([url, token, org, bucket]):
            raise ValueError("Missing required InfluxDB configuration.")
        self.client = InfluxDBClient(url=url, token=token, org=org, verify_ssl=False)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = bucket
        self.org = org
        logging.info("Connected to InfluxDB")

    def connect(self):
        self.client = InfluxDBClient(
            url=self.config["url"],
            token=self.config["token"],
            org=self.config["org"]
        )
        self.query_api = self.client.query_api()

    def query(self, flux_query):
        result = self.query_api.query_data_frame(flux_query)
        return result

    def close(self):
        self.client.__del__()