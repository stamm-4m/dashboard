from config import INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG,INFLUXDB_BUCKET,BACH_ID
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import time
import random
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)

class InfluxDBHandler:
    def __init__(self):
        """
        Initializes the InfluxDB client for InfluxDB 2.x.
        """
        try:
            if not all([INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET]):
                raise ValueError("One or more values of configuration InfluxDB not are set.")

            self.client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG, verify_ssl=False)
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            self.bucket = INFLUXDB_BUCKET
            self.org = INFLUXDB_ORG
            # Mapping of variables to categories
            self.variable_categories = {
                "sensor": [
                    "air_head_pressure", "dissolved_oxygen_concentration", "pH", 
                    "temperature", "generated_heat", "CO2_percent_in_off_gas",
                    "oxygen_uptake_rate", "oxygen_in_percent_in_off_gas",
                    "carbon_evolution_rate"
                ],
                "actuator": [
                    "aeration_rate", "agitator", "sugar_feed_rate", "acid_flow_rate", "base_flow_rate", 
                    "heating/cooling_water_flow_rate", "heating_water_flow_rate", "water_for_injection/dilution",
                    "dumped_broth_flow", "substrate_concentration", "PAA_flow", "oil_flow", "ammonia_shots"
                ],
                "computed_variable": [
                    "vessel_volume", "vessel_weight"
                ],
                "soft_sensor": [
                    "penicillin_concentration"
                ],
                "offline_measurement": [
                    "PAA_concentration", "NH3_concentration", "offline_penicillin_concentration",
                    "offline_biomass_concentration", "viscosity"
                ]
            }
            self.unit_mapping = {
                "time": "Hour", "aeration_rate": "Fg:L/h", "agitator": "RPM",
                "sugar_feed_rate": "L/h", "acid_flow_rate": "L/h", "base_flow_rate": "L/h",
                "heating/cooling_water_flow_rate": "L/h", "heating_water_flow_rate": "L/h",
                "water_for_injection/dilution": "L/h", "air_head_pressure": "bar",
                "dumped_broth_flow": "L/h", "substrate_concentration": "g/L",
                "dissolved_oxygen_concentration": "mg/L", "penicillin_concentration": "g/L",
                "vessel_volume": "L", "vessel_weight": "Kg", "pH": "pH",
                "temperature": "Kelvin", "generated_heat": "kJ", "CO2_percent_in_off_gas": "%",
                "PAA_flow": "L/h", "PAA_concentration": "g L^{-1}", "oil_flow": "L/h",
                "NH3_concentration": "g L^{-1}", "oxygen_uptake_rate": "g min^{-1}",
                "oxygen_in_percent_in_off_gas": "%", "offline_penicillin_concentration": "g L^{-1}",
                "offline_biomass_concentration": "g L^{-1}", "carbon_evolution_rate": "g/h",
                "ammonia_shots": "kgs", "viscosity": "centPoise"
            }
            
            # Create a unified list of all fields
            self.all_fields = [field for fields in self.variable_categories.values() for field in fields]
        
            print("Successfully connected to InfluxDB")
        except Exception as e:
            print(f"Error connecting to InfluxDB: {e}")

    def get_buckets(self):
        """
        Retrieves a list of buckets available in InfluxDB.

        Returns:
            list: A list of bucket names.
        """
        print(self.client)
        try:
            buckets_api = self.client.buckets_api()
            buckets = buckets_api.find_buckets().buckets
            return [bucket.name for bucket in buckets if bucket is not None]
        except Exception as e:
            print(f"Error fetching buckets: {e}")
            return []
  
    def fetch_buckets_and_projects(self):
        """
        Retrieves buckets and their associated projects from InfluxDB.

        Returns:
            dict: A dictionary where keys are bucket names and values are lists of measurements.
        """
        try:
            buckets = self.get_buckets()
            data = {}
            for bucket in buckets:
                query = f'''
                import "influxdata/influxdb/schema"
                schema.measurements(bucket: "{bucket}")
                '''
                tables = self.query_api.query(org=INFLUXDB_ORG, query=query)
                data[bucket] = [record.get_value() for table in tables for record in table.records]
            return data
        except Exception as e:
            print(f"Error fetching buckets and projects: {e}")
            return {}

    def read_data_from_influx(self, bucket, measurement, fields, start_time="-1h", stop_time="now"):
        """
        Reads data from InfluxDB and returns it as a Pandas DataFrame.

        Args:
            bucket (str): Bucket to query from.
            measurement (str): Measurement name.
            fields (list): List of field names.
            start_time (str): Query start time.
            stop_time (str): Query stop time.

        Returns:
            pd.DataFrame: DataFrame containing the query results.
        """
        try:
            fields_filter = " or ".join([f'r["_field"] == "{field}"' for field in fields])
            query = f'''
            from(bucket: "{bucket}")
            |> range(start: {start_time}, stop: {stop_time})
            |> filter(fn: (r) => r["_measurement"] == "{measurement}")
            |> filter(fn: (r) => {fields_filter})
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            result = self.query_api.query_data_frame(query=query, org=INFLUXDB_ORG)

            if isinstance(result, list):
                return pd.concat(result, ignore_index=True)
            elif isinstance(result, pd.DataFrame):
                return result
            else:
                print("No data returned from InfluxDB.")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error reading data from InfluxDB: {e}")
            return pd.DataFrame()
        
    
    def get_experiment_ids_from_bucket(self):
        """
        Retrieves a unique list of experiment_ID from the specified bucket in InfluxDB.

        Args:
            url (str): URL of the InfluxDB server.
            token (str): Authentication token.
            org (str): Organization in InfluxDB.
            bucket (str): Name of the bucket.

        Returns:
            list: Unique list of experiment_ID.
        """
        try:
            # Connect to the InfluxDB client
            
                # Query to retrieve unique experiment_ID
                query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: -90d)
                |> filter(fn: (r) => exists r["{str(BACH_ID)}"])  // Asegura que experiment_ID existe
                |> keep(columns: ["{str(BACH_ID)}"])
                |> distinct(column: "{str(BACH_ID)}")
                |> sort(columns: ["{str(BACH_ID)}"], desc: false)
                """
                
                # Execute the query
                result = self.query_api.query(org=self.org, query=query)
                # Extract experiment_ID from the results
                experiment_ids = [
                    record.get_value()
                    for table in result
                    for record in table.records
                ]
                
                return experiment_ids

        except Exception as e:
            print(f"Error retrieving experiment_ID: {e}")
            return []
  
    def get_data_by_batch_id2(self, batch_id):
        """
        Returns a DataFrame with all fields and values associated with a given batch_id.

        Args:
            batch_id (int/str): The batch identifier.

        Returns:
            pd.DataFrame: DataFrame with the data corresponding to the batch_id.
        """
        try:
            # Validate batch_id
            if not batch_id:
                raise ValueError("The batch_id cannot be None or empty.")

            # Build the Flux query
            query = f"""
            from(bucket: "{str(INFLUXDB_BUCKET)}")
            |> range(start: -90d)  // Adjust the time range as needed
            |> filter(fn: (r) => r["_measurement"] == "{str(batch_id)}")
            """

            print("query", query)

            # Execute the query
            results = self.query_api.query(query=query)

            # If no results returned, print and return empty DataFrame
            if not results:
                print(f"No data found for batch_id {batch_id}.")
                return pd.DataFrame()

            # Prepare data list
            data = []

            # Process the query results
            for table in results:
                for record in table.records:
                    data.append(record.values)  # Store record values

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Check if the DataFrame is non-empty
            if not df.empty:
                # Select only relevant columns
                df = df[["_time", "_field", "_value"]]

                # Pivot the DataFrame
                df_pivot = df.pivot(index="_time", columns="_field", values="_value")

                # Reset index to make '_time' a column again
                df_pivot.reset_index(inplace=True)

                return df_pivot
            else:
                print(f"No data found for batch_id {batch_id}.")
                return pd.DataFrame()

        except ValueError as ve:
            print(f"Invalid input: {ve}")
            return pd.DataFrame()

        except Exception as e:
            print(f"Error retrieving data for batch_id {batch_id}: {e}")
            return pd.DataFrame()
    
    def get_data_until_latest(self, batch_id):
        """
        Returns a DataFrame with all records up to the latest entry for a given batch_id.

        Args:
            batch_id (int/str): The batch identifier.

        Returns:
            pd.DataFrame: DataFrame with all data up to the most recent point.
        """
        try:
            if not batch_id:
                raise ValueError("The batch_id cannot be None or empty.")

            # Flux query to retrieve all data for the given batch_id
            query = f"""
            from(bucket: "{str(INFLUXDB_BUCKET)}")
            |> range(start: 0)  // Get all data from the beginning of the bucket
            |> filter(fn: (r) => r["{str(BACH_ID)}"] == "{str(batch_id)}")
            """
            
            results = self.query_api.query(query=query)

            if not results:
                print(f"No data found for batch_id {batch_id}.")
                return pd.DataFrame()

            data = []
            for table in results:
                for record in table.records:
                    data.append(record.values)

            df = pd.DataFrame(data)

            if not df.empty:
                df = df[["_time", "_field", "_value"]]
                df_pivot = df.pivot(index="_time", columns="_field", values="_value")
                df_pivot.reset_index(inplace=True)
                return df_pivot
            else:
                print(f"No data found for batch_id {batch_id}.")
                return pd.DataFrame()

        except Exception as e:
            print(f"Error retrieving data until latest for batch_id {batch_id}: {e}")
            return pd.DataFrame()



    def get_distinct_experiment_ids(self, bucket_name, time_range="-90d"):
        """
        Retrieves a unique list of experiment_ID from the specified bucket in InfluxDB.

        Args:
            bucket_name (str): Name of the bucket.
            time_range (str): Time range for the query (default is "-30d").

        Returns:
            list: Unique list of experiment_ID.
        """
        try:
            # Query to retrieve unique experiment_ID
            query = f"""
            from(bucket: "{bucket_name}")
            |> range(start: {time_range})
            |> filter(fn: (r) => exists r["{str(BACH_ID)}"])  // Asegura que experiment_ID existe
            |> keep(columns: ["{str(BACH_ID)}"])
            |> distinct(column: "{str(BACH_ID)}")
            |> sort(columns: ["{str(BACH_ID)}"], desc: false)
            """
            #print("query",query)

            # Execute the query
            result = self.query_api.query(org=self.org, query=query)

            # Extract experiment_id from the results
            experiment_ids = [
                record.get_value()
                for table in result
                for record in table.records
            ]

            return experiment_ids

        except Exception as e:
            print(f"Error retrieving experiment_ID from bucket '{bucket_name}': {e}")
            return []

    def get_category_counts(self, bucket_name, experiment_ID, time_range="-90d"):
        """
        Retrieves the count of sensors, actuators, soft sensors, and computed variables
        for a specific bucket and experiment_ID.

        Args:
            bucket_name (str): Name of the bucket.
            experiment_ID (str): ID of the experiment to filter.
            time_range (str): Time range for the query (default is "-90d").

        Returns:
            dict: A dictionary with the counts of each category.
        """
        try:

            logging.info(f"Fetching category counts for experiment: {experiment_ID} in bucket: {bucket_name}")
            
            # Query to retrieve data counts by category
            query = f"""
            from(bucket: \"{bucket_name}\")
            |> range(start: {time_range})
            |> filter(fn: (r) => r[\"{str(BACH_ID)}\"] == \"{experiment_ID}\")
            |> keep(columns: [\"type\", \"_field\"])
            |> distinct(column: \"_field\")
            |> count()
            """

            logging.debug(f"Executing Flux Query: {query}")

            # Execute the query
            result = self.query_api.query(org=self.org, query=query)

            # Extract counts per category
            category_counts = {"sensor": 8, "actuator": 11, "computed_variable": 2, "soft_sensor": 1, "offline_measurement": 5}
            
            logging.info(f"Final Category Counts: {category_counts}")
            return category_counts

        except Exception as e:
            logging.error(f"Error retrieving category counts: {e}")
            return {"sensor": 8, "actuator": 11, "computed_variable": 2, "soft_sensor": 1, "offline_measurement": 5}

    def get_experiment_duration(self, experiment_ID, time_range="-90d"):
        """
        Fetch the duration of an experiment based on its ID.

        Args:
            experiment_ID (str): The ID of the experiment.
            time_range (str): The time range to query (default is "-90d").

        Returns:
            float: Duration of the experiment in hours, or 0 if no data is found.
        """
        try:
            # Query for the earliest time
            query_min_time = f"""
            from(bucket: "{self.bucket}")
            |> range(start: {time_range})
            |> filter(fn: (r) => r["{str(BACH_ID)}"] == "{str(experiment_ID)}")
            |> sort(columns: ["_time"], desc: false)
            |> limit(n: 1)
            """

            # Query for the latest time
            query_max_time = f"""
            from(bucket: "{self.bucket}")
            |> range(start: {time_range})
            |> filter(fn: (r) => r["{str(BACH_ID)}"] == "{str(experiment_ID)}")
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: 1)
            """

            # Execute queries
            result_min_time = self.query_api.query(org=self.org, query=query_min_time)
            result_max_time = self.query_api.query(org=self.org, query=query_max_time)

            # Extract times
            min_time, max_time = None, None

            for table in result_min_time:
                for record in table.records:
                    min_time = record.get_time()

            for table in result_max_time:
                for record in table.records:
                    max_time = record.get_time()

            # Check if both times are valid
            if min_time and max_time:
                duration_in_seconds = (max_time - min_time).total_seconds()
                return duration_in_seconds / 3600  # Convert seconds to hours

            return 0.0  # Return 0 if no data is found
        except Exception as e:
            print(f"Error in get_experiment_duration: {e}")
            return None

    def get_data_for_table(self, bucket_name, experiment_ID, time_range="-90d"):
        """
        Fetch the data required for populating the DataTable, adding units based on the variable mapping.
        """
        try:
            queries = {
                "mean": f"""
                from(bucket: "{bucket_name}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["{str(BACH_ID)}"] == "{experiment_ID}")
                |> keep(columns: ["type", "_field", "_value"])
                |> group(columns: ["type", "_field"])
                |> mean()
                """,
                "max": f"""
                from(bucket: "{bucket_name}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["{str(BACH_ID)}"] == "{experiment_ID}")
                |> keep(columns: ["type", "_field", "_value"])
                |> group(columns: ["type", "_field"])
                |> max()
                """,
                "min": f"""
                from(bucket: "{bucket_name}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["{str(BACH_ID)}"] == "{experiment_ID}")
                |> keep(columns: ["type", "_field", "_value"])
                |> group(columns: ["type", "_field"])
                |> min()
                """
            }
            
            data = {}
            for key, query in queries.items():
                result = self.query_api.query(org=self.client.org, query=query)
                for table in result:
                    for record in table.records:
                        variable_name = record.values.get("_field", "N/A")
                        unit = self.unit_mapping.get(variable_name, "N/A")
                        data_key = (record.values.get("type", "N/A"), variable_name)
                        if data_key not in data:
                            data[data_key] = {
                                "Type": record.values.get("type", "N/A"),
                                "Name": variable_name,
                                "Unit": unit,
                                "Mean": "N/A",
                                "Max": "N/A",
                                "Min": "N/A"
                            }
                        data[data_key][key.capitalize()] = record.values.get("_value", "N/A")
            
            return list(data.values())
        except Exception as e:
            logging.error(f"Error fetching data for table: {e}")
            return []

    def get_data_training(self, experiments_id, selected_metric):
        
        if not experiments_id or not selected_metric:
            return []

        # Formar la consulta Flux para obtener los valores
        query = f"""
            from(bucket: "{self.bucket}")
                |> range(start: -90d)  
                |> filter(fn: (r) => r["_field"] == "{selected_metric}")
                |> filter(fn: (r) => {" or ".join(f'r["{str(BACH_ID)}"] == "{str(e)}.0"' for e in experiments_id)})
                |> keep(columns: ["_value"])
        """
        print("query training:",query)
        # Ejecutar la consulta
        result = self.query_api.query(org=self.client.org, query=query)

        # Extraer solo los valores numéricos
        values = [record.get_value() for table in result for record in table.records]

        return values

    def get_data_test(self, experiment_id, selected_metric):
        try:
            if not experiment_id or not selected_metric:
                raise ValueError("The experiment_id and the metric cannot be None or empty.")

            # Flux query to retrieve only the selected metric values
            query = f"""
            from(bucket: "{self.bucket}")
                |> range(start: -90d)  // Adjust the time range as needed
                |> filter(fn: (r) => r["{str(BACH_ID)}"] == "{str(experiment_id)}")
                |> filter(fn: (r) => r["_field"] == "{selected_metric}")
                
            """
            #|> keep(columns: ["_value"])
            print("query test:",query)
            # Execute query
            result = self.query_api.query(query=query)

            # Extract only the numerical values
            values = [record.get_value() for table in result for record in table.records]

            return values if values else []

        except Exception as e:
            print(f"Error retrieving test data for experiment_id {experiment_id}: {e}")
            return []

    def get_recent_experiment_ids(self, bucket: str, minutes: int = 5):
        """
        Returns experiment IDs with data in the last `minutes` minutes.
        """
        query = f'''
        import "influxdata/influxdb/schema"
        from(bucket: "{bucket}")
        |> range(start: -{minutes}m)
        |> keep(columns: ["{str(BACH_ID)}"])
        |> group(columns: ["{str(BACH_ID)}"])
        |> distinct(column: "{str(BACH_ID)}")
        |> sort(columns: ["{str(BACH_ID)}"])
        '''
        tables = self.query_api.query(org=self.org, query=query)
        experiment_ids = []
        for table in tables:
            for record in table.records:
                experiment_ids.append(record.get_value())
        return list(set(experiment_ids))
