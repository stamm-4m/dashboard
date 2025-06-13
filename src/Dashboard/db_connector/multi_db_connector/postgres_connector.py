"""
Created on Wed May 14 10:15:12 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr

"""

import psycopg2
import pandas as pd
from .base import BaseDBConnector

class PostgresConnector(BaseDBConnector):
    def connect(self):
        self.conn = psycopg2.connect(
            dbname=self.config["dbname"],
            user=self.config["user"],
            password=self.config["password"],
            host=self.config["host"],
            port=self.config.get("port", 5432)
        )
        self.cursor = self.conn.cursor()

    def query(self, sql_query):
        return pd.read_sql_query(sql_query, self.conn)

    def close(self):
        self.cursor.close()
        self.conn.close()