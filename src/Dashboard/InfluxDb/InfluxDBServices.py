from Dashboard.config import  ( INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG,INFLUXDB_PROJECT_NAME,INFLUXDB_BATCH_ID,
                               INFLUXDB_BUCKET_METADATA,INFLUXDB_BUCKET_PREDICTIONS,INFLUXDB_BUCKET_RAW,INFLUXDB_MEASUREMENT,
                               INFLUXDB_DEVICE_ID)
                            
from Dashboard.db_connector.multi_db_connector.influxdb_connector import InfluxDBConnector
from influxdb_client import Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta

import pandas as pd
import logging

logger = logging.getLogger(__name__)

config = {
    "url":INFLUXDB_URL,
    "token":INFLUXDB_TOKEN,
    "org":INFLUXDB_ORG,
}

class InfluxDBServices:
    def __init__(self):
        self.connector = InfluxDBConnector(config)
        self.buckets = {
            "RAW": INFLUXDB_BUCKET_RAW,
            "PREDICTIONS": INFLUXDB_BUCKET_PREDICTIONS,
            "METADATA": INFLUXDB_BUCKET_METADATA,
        }
        self.observed_properties = self.get_all_observed_properties()

        # Crear el mapping de unidades, por ejemplo:
        self.unit_mapping = {
            prop: meta["unit"]
            for prop, meta in self.observed_properties.items()
            if meta["unit"] is not None
        }
        
    def get_all_observed_properties(self):
        """
        Retrieves all observed properties and their metadata (unit, display_name, decimals)
        from the InfluxDB metadata bucket.

        Returns:
            dict: Mapping of observed_property -> {"unit": str, "display_name": str, "decimals": int}
        """
        try:
            query = f"""
            from(bucket: "{self.buckets['METADATA']}")
            |> range(start: 0)
            |> filter(fn: (r) => r["_measurement"] == "{str(INFLUXDB_MEASUREMENT)}")
            |> filter(fn: (r) => r["_field"] == "decimals" or r["_field"] == "display_name" or r["_field"] == "unit")
            |> last()
            |> group(columns: ["observed_property", "_field"])
            |> pivot(rowKey:["observed_property"], columnKey: ["_field"], valueColumn: "_value")
            """

            result = self.connector.query_api.query(query)

            observed_props = {}
            for table in result:
                for record in table.records:
                    obs = record.values.get("observed_property")
                    unit = record.values.get("unit")
                    display_name = record.values.get("display_name")
                    decimals = record.values.get("decimals")
                    observed_props[obs] = {
                        "unit": unit,
                        "display_name": display_name,
                        "decimals": decimals
                    }

            return observed_props

        except Exception as e:
            logger.error(f"Error retrieving observed properties: {e}")
            return {}

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
                from(bucket: "{self.buckets["RAW"]}")
                |> range(start: 0)
                |> filter(fn: (r) => exists r["{str(INFLUXDB_BATCH_ID)}"])  // Asegura que experiment_ID existe
                |> keep(columns: ["{str(INFLUXDB_BATCH_ID)}"])
                |> distinct(column: "{str(INFLUXDB_BATCH_ID)}")
                |> sort(columns: ["{str(INFLUXDB_BATCH_ID)}"], desc: false)
                """
                
                # Execute the query
                result = self.connector.query_api.query(org=self.connector.org, query=query)
                # Extract experiment_ID from the results
                experiment_ids = [
                    record.get_value()
                    for table in result
                    for record in table.records
                ]
                
                return experiment_ids

        except Exception as e:
            logger.error(f"Error retrieving experiment_ID: {e}")
            return []
  
    def get_data_by_batch_id(self, batch_id, minutes: int = 0):
        """
        Returns a DataFrame with all fields and values associated with a given batch_id.

        Args:
            batch_id (int/str): The batch identifier.
            minutes (int, optional): 
            - 0 -> fetch all data
            - n > 0 -> fetch data from the last n minutes
        Returns:
            pd.DataFrame: DataFrame with the data corresponding to the batch_id.
        """
        try:
            # Validate batch_id
            if not batch_id:
                raise ValueError("The batch_id cannot be None or empty.")
            
            # Build time range part
            if minutes == 0 or minutes == 5:
                start_flux = "-inf"
            else:
                start_flux = f"-{minutes}m"
            # Build the Flux query
            query = f"""
            from(bucket: "{str(self.buckets["RAW"])}")
            |> range(start: {str(start_flux)})  // Adjust the time range as needed
            |> filter(fn: (r) => r["{str(INFLUXDB_BATCH_ID)}"] == "{str(batch_id)}")
            """

            #print("query", query)

            # Execute the query
            results = self.connector.query_api.query(query=query)

            # If no results returned, print and return empty DataFrame
            if not results:
                logger.debug(f"No data found for batch_id {batch_id}.")
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
                df = df[["_time", "observed_property", "_value"]]

                # Pivot the DataFrame
                df_pivot = df.pivot(index="_time", columns="observed_property", values="_value")

                # Reset index to make '_time' a column again
                df_pivot.reset_index(inplace=True)

                return df_pivot
            else:
                logger.info(f"No data found for batch_id {batch_id}.")
                return pd.DataFrame()

        except ValueError as ve:
            logger.error(f"Invalid input: {ve}")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error retrieving data for batch_id {batch_id}: {e}")
            return pd.DataFrame()
    
    def get_data_until_latest(self, batch_id):
        """
        Returns a DataFrame with one row per timestamp, containing:
        - Raw values for each observed property.
        - A single predicted value column (penicillin concentration).

        Args:
            batch_id (int | str): The batch identifier.

        Returns:
            pd.DataFrame: Combined table with '_time' as index.
        """
        try:
            if not batch_id:
                raise ValueError("The batch_id cannot be None or empty.")

            # Flux query
            raw_query = f"""
                from(bucket: "stamm_raw")
                |> range(start: 0)
                |> filter(fn: (r) => r["batch_id"] == "{batch_id}")
                |> filter(fn: (r) => r["_measurement"] == "{str(INFLUXDB_MEASUREMENT)}")
                |> filter(fn: (r) => r["project_name"] == "{str(INFLUXDB_PROJECT_NAME)}")
                |> filter(fn: (r) => r["device_id"] == "{str(INFLUXDB_DEVICE_ID)}")
                |> rename(columns: {{_value: "raw_value"}})
                |> keep(columns: ["_time", "observed_property", "raw_value"])
                |> pivot(rowKey:["_time"], columnKey: ["observed_property"], valueColumn: "raw_value")
                """

            pred_query = f"""
                from(bucket: "stamm_predictions")
                |> range(start: 0)
                |> filter(fn: (r) => r["batch_id"] == "{batch_id}")
                |> filter(fn: (r) => r["_measurement"] == "{str(INFLUXDB_MEASUREMENT)}")
                |> filter(fn: (r) => r["project_name"] == "{str(INFLUXDB_PROJECT_NAME)}")
                |> filter(fn: (r) => r["device_id"] == "{str(INFLUXDB_DEVICE_ID)}")
                |> rename(columns: {{_value: "prediction_value"}})
                |> keep(columns: ["_time", "model_id", "prediction_value"])
                |> pivot(rowKey:["_time"], columnKey: ["model_id"], valueColumn: "prediction_value")
                """
           
            df_raw = self.connector.query_api.query_data_frame(raw_query)
            df_pred = self.connector.query_api.query_data_frame(pred_query)
            if df_raw.empty and df_pred.empty:
                logger.info(f"No data found for batch_id {batch_id}.")
                return pd.DataFrame()
            
            # --- Prepare DataFrames ---
            df_raw["_time"] = pd.to_datetime(df_raw["_time"])
            df_pred["_time"] = pd.to_datetime(df_pred["_time"])

            # --- Set _time as index ---
            df_raw = df_raw.set_index("_time").sort_index()
            df_pred = df_pred.set_index("_time").sort_index()

            # --- Merge raw + predictions by nearest timestamp ---
            df_final = pd.merge_asof(df_raw, df_pred, left_index=True, right_index=True, direction="nearest")

            df_final = df_final.reset_index()
            df_final = df_final.drop(columns=["result_x", "result_y", "table_x", "table_y"], errors="ignore")

            return df_final

        except Exception as e:
            logger.error(f"Error retrieving data until latest for batch_id {batch_id}: {e}")
            return pd.DataFrame()

    def get_distinct_experiment_ids(self, project_name="", time_range="0"):
        """
        Retrieves a unique list of experiment_ID from the specified bucket in InfluxDB.

        Args:
            bucket_name (str): Name of the bucket.
            time_range (str): Time range for the query (default is "-30d").

        Returns:
            list: Unique list of experiment_ID.
        """
        filter_project = f'|> filter(fn: (r) => r["project_name"] == "{project_name}")' if project_name else ""

        try:
            # Query to retrieve unique experiment_ID
            query = f"""
            from(bucket: "{self.buckets["RAW"]}")
            |> range(start: {time_range})
            {filter_project}
            |> filter(fn: (r) => exists r["{str(INFLUXDB_BATCH_ID)}"])
            |> keep(columns: ["{str(INFLUXDB_BATCH_ID)}"])
            |> distinct(column: "{str(INFLUXDB_BATCH_ID)}")
            |> sort(columns: ["{str(INFLUXDB_BATCH_ID)}"], desc: false)
            """
            #print("query",query)

            # Execute the query
            result = self.connector.query_api.query(org=self.connector.org, query=query)

            # Extract experiment_id from the results
            experiment_ids = [
                record.get_value()
                for table in result
                for record in table.records
            ]

            return experiment_ids

        except Exception as e:
            logger.error(f"Error retrieving experiment_ID from bucket '{INFLUXDB_BUCKET_RAW}': {e}")
            return []

    
    def get_experiment_duration(self, experiment_ID, time_range="0"):
        """
        Fetch the duration of an experiment based on its ID.

        Args:
            experiment_ID (str): The ID of the experiment.
            time_range (str): Time range for the search (default "-100d").

        Returns:
            float: Duration in hours, or 0 if not found.
        """
        try:
            # Query for earliest timestamp
            query_min_time = f"""
            from(bucket: "{self.buckets["RAW"]}")
            |> range(start: 0)
            |> filter(fn: (r) => r[\"{str(INFLUXDB_BATCH_ID)}\"] == "{experiment_ID}")
            |> keep(columns: ["_time"])
            |> sort(columns: ["_time"], desc: false)
            |> limit(n: 1)
            """

            # Query for latest timestamp
            query_max_time = f"""
            from(bucket: "{self.buckets["RAW"]}")
            |> range(start: 0)
            |> filter(fn: (r) => r[\"{str(INFLUXDB_BATCH_ID)}\"] == "{experiment_ID}")
            |> keep(columns: ["_time"])
            |> sort(columns: ["_time"], desc: true)
            |> limit(n: 1)
            """
            # Execute
            result_min_time = self.connector.query_api.query(org=self.connector.org, query=query_min_time)
            result_max_time = self.connector.query_api.query(org=self.connector.org, query=query_max_time)
            
            # Parse times
            for table in result_min_time:
                for record in table.records:
                    min_time = record.get_time()

            for table in result_max_time:
                for record in table.records:
                    max_time = record.get_time()

            logger.debug(f"Min time: {min_time}, Max time: {max_time}")

            if min_time and max_time:
                duration_in_seconds = (max_time - min_time).total_seconds()
                return duration_in_seconds / 3600

            # Compute
            if min_time and max_time:
                duration_seconds = (max_time - min_time).total_seconds()
                return round(duration_seconds / 3600, 2)  # Duration in hours

            return 0.0

        except Exception as e:
            logger.info(f"get_experiment_duration: {e}")
            return 0.0

    def get_data_for_table(self, experiment_ID, time_range="0"):
        """
        Fetch the data required for populating the DataTable, adding units based on the variable mapping.
        Numeric values are rounded to 4 decimals when applicable.
        """
        try:
            queries = {
                "mean": f"""
                from(bucket: "{self.buckets['RAW']}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["batch_id"] == "{experiment_ID}")
                |> keep(columns: ["device_id", "observed_property", "source", "_field", "_value"])
                |> group(columns: ["device_id", "observed_property", "source", "_field"])
                |> mean()
                """,

                "max": f"""
                from(bucket: "{self.buckets['RAW']}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["batch_id"] == "{experiment_ID}")
                |> keep(columns: ["device_id", "observed_property", "source", "_field", "_value"])
                |> group(columns: ["device_id", "observed_property", "source", "_field"])
                |> max()
                """,

                "min": f"""
                from(bucket: "{self.buckets['RAW']}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["batch_id"] == "{experiment_ID}")
                |> keep(columns: ["device_id", "observed_property", "source", "_field", "_value"])
                |> group(columns: ["device_id", "observed_property", "source", "_field"])
                |> min()
                """
            }
            
            data = {}
            for key, query in queries.items():
                result = self.connector.query_api.query(org=self.connector.org, query=query)
                for table in result:
                    for record in table.records:
                        variable_name = record.values.get("observed_property", "N/A")
                        unit = self.unit_mapping.get(variable_name, "N/A")
                        data_key = (record.values.get("source", "N/A"), variable_name)
                        
                        if data_key not in data:
                            data[data_key] = {
                                "Type": record.values.get("source", "N/A"),
                                "Name": variable_name,
                                "Unit": unit,
                                "Mean": "N/A",
                                "Max": "N/A",
                                "Min": "N/A"
                            }

                        value = record.values.get("_value", "N/A")
                        # Redondear si es numérico
                        if isinstance(value, (int, float)):
                            value = round(value, 4)

                        data[data_key][key.capitalize()] = value
            data = {
                k: v for k, v in data.items()
                if v.get("Name") != "experiment_time"
            }
            return list(data.values())

        except Exception as e:
            logger.error(f"Error fetching data for table: {e}")
            return []


    def get_data_training(self, experiments_id, selected_metric):
        """
        Get training data from InfluxDB

        Args:
            experiments_id (list): List of experiment IDs.
            selected_metric (str): Metric name to filter.

        Returns:
            list[list]: 2D list with numeric values only (no timestamps).
        """
        if not experiments_id:
            return []

        logger.debug(f"selected_metric: {selected_metric}")

        # Filtro por métrica si se selecciona una
        metric_filter = f'|> filter(fn: (r) => r["observed_property"] == "{selected_metric}")' if selected_metric else ""

        # Consulta Flux
        query = f'''
            from(bucket: "{self.buckets["RAW"]}")
                |> range(start: 0)
                |> filter(fn: (r) => {" or ".join(f'r["{str(INFLUXDB_BATCH_ID)}"] == "{str(e)}"' for e in experiments_id)})
                {metric_filter}
                |> keep(columns: ["_time", "_value", "observed_property"])
                |> pivot(rowKey: ["_time"], columnKey: ["observed_property"], valueColumn: "_value")
                |> sort(columns: ["_time"])
        '''
        # Ejecutar consulta
        result = self.connector.query_api.query(org=self.connector.org, query=query)

        # Extraer nombres de columnas y registros
        records = [record.values for table in result for record in table.records]

        if not records:
            return []

        # Obtener solo las columnas numéricas (excluyendo "_time" y tags)
        value_keys = [key for key in records[0].keys() if key not in ["_time", "result", "table"]]

        # Convertimos en lista de listas
        data = [[rec.get(k, float('nan')) for k in value_keys] for rec in records]

        return data

    
    def get_data_test(self, experiment_id, selected_metric, range_slider=None):
        """
        Get test data from InfluxDB with optional time-window filtering.

        Args:
            experiment_id (str|int): Experiment ID.
            selected_metric (str): Metric name to filter.
            range_slider (list[int], optional): [start_idx, end_idx] indices for time-window.
                If None, all data is returned.

        Returns:
            np.ndarray: 2D array (rows = observations, columns = fields).
        """
        try:
            if not experiment_id:
                raise ValueError("The experiment_id cannot be None or empty.")

            # Filtro por métrica solo si se proporciona
            metric_filter = f'|> filter(fn: (r) => r["observed_property"] == "{selected_metric}")' if selected_metric else ""

            # Flux query
            query = f"""
                from(bucket: "{self.buckets["RAW"]}")
                    |> range(start: 0)
                    |> filter(fn: (r) => r["{str(INFLUXDB_BATCH_ID)}"] == "{str(experiment_id)}")
                    {metric_filter}
                    |> keep(columns: ["_time", "_value", "observed_property"])
            """

            # Ejecutar la consulta
            result = self.connector.query_api.query(query=query)

            # Agrupar valores por _field
            field_values = {}
            for table in result:
                for record in table.records:
                    field = record.values.get("observed_property")
                    value = record.get_value()
                    field_values.setdefault(field, []).append(value)

            if not field_values:
                return []

            # Ajustar longitudes (rellenar con NaN donde falten datos)
            max_len = max(len(values) for values in field_values.values())
            for field, values in field_values.items():
                if len(values) < max_len:
                    field_values[field].extend([np.nan] * (max_len - len(values)))

            # Armar array 2D (cada columna es un _field, cada fila una observación)
            import numpy as np
            sorted_fields = sorted(field_values.keys())
            matrix = np.column_stack([field_values[field] for field in sorted_fields])

            # ✅ Filtrar por range_slider
            if range_slider is not None and len(range_slider) == 2:
                start_idx, end_idx = range_slider
                if 0 <= start_idx < matrix.shape[0] and 0 < end_idx <= matrix.shape[0]:
                    matrix = matrix[start_idx:end_idx, :]
                else:
                    logger.debug("⚠️ range_slider fuera de rango en get_data_test, devolviendo todo el dataset")

            return matrix

        except Exception as e:
            logger.error(f"Error retrieving test data for experiment_id {experiment_id}: {e}")
        return []



    def get_data_experiment_id(self, experiment_id: str, minutes: int = 5) -> pd.DataFrame:
        """
        Retrieves data for a specific experiment_id from InfluxDB in the last N minutes.

        Args:
            experiment_id (str): The experiment_id to filter.
            minutes (int): Time window in minutes to look back.

        Returns:
            pd.DataFrame: A DataFrame with the data for the given experiment_id.
        """
        try:
            # Build Flux query
            query = f'''
            from(bucket: "{self.buckets["RAW"]}")
            |> range(start: -{minutes}m)
            |> filter(fn: (r) => r["{str(INFLUXDB_BATCH_ID)}"] == "{experiment_id}")
            |> limit(n: 1)  // Stop early as we only need to check for existence
            '''

            result = self.connector.query_api.query(org=self.connector.org, query=query)

            # Parse result into a DataFrame
            records = [
                record.values
                for table in result
                for record in table.records
            ]

            df = pd.DataFrame(records)
            return df

        except Exception as e:
            logger.error(f"get_data_experiment_id('{experiment_id}', {minutes}): {e}")
            return pd.DataFrame()

    def get_online_experiments_summary(self, time_unit="minutes", time_value=5):
        """
        Retrieves a summary of online experiments based on the specified time window.

        Args:
            time_unit (str): Time unit for filtering ('seconds', 'minutes', 'hours', 'days', 'months').
            time_value (int): Numeric value representing the amount of time to look back.

        Returns:
            list: List of dictionaries summarizing experiment data (ID, Date, Batch Size, Yields, Temperature).
        """
        try:
            if not time_unit or not time_value:
                logger.warning("Invalid time range parameters.")
                return []

            # Map full unit to InfluxDB shorthand
            unit_map = {
                "seconds": "s",
                "minutes": "m",
                "hours": "h",
                "days": "d",
                "months": "mo"
            }

            if time_unit not in unit_map:
                logger.warning(f"Unsupported time unit: {time_unit}")
                return []

            shorthand = unit_map[time_unit]
            flux_query = f"""
            from(bucket: "{self.buckets["RAW"]}")
            |> range(start: -{time_value}{shorthand})
            |> filter(fn: (r) => exists r["batch_id"])
            |> keep(columns: ["_time", "_value", "batch_id", "device_id", "observed_property"])
            |> group(columns: ["batch_id"])
            |> pivot(rowKey:["_time"], columnKey: ["observed_property"], valueColumn: "_value")
            """

            result = self.connector.query_api.query_data_frame(flux_query)

            if isinstance(result, list):
                if not result:
                    #print("[INFO] No recent data found.")
                    return []
                df = pd.concat(result, ignore_index=True)
            else:
                df = result
            if df.empty:
                #print("[INFO] No recent data found.")
                return []

            if "batch_id" not in df.columns:
                logger.warning("No experiment ID field found.")
                return []

            experiment_ids = df["batch_id"].unique()
            results = []

            for exp_id in experiment_ids:
                df_exp = df[df["batch_id"] == exp_id]
                batch_size = int(df_exp.shape[0])
                start_time = df_exp["_time"].min()
                end_time = df_exp["_time"].max()

                start_str = pd.to_datetime(start_time).strftime("%Y-%m-%d %H:%M:%S") if pd.notna(start_time) else "N/A"
                end_str = pd.to_datetime(end_time).strftime("%Y-%m-%d %H:%M:%S") if pd.notna(end_time) else "N/A"

                results.append({
                    "Experiment ID": exp_id,
                    "Start Time": start_str,
                    "End Time": end_str,
                    "Batch size": batch_size
                })

            return results

        except Exception as e:
            logger.error(f"get_online_experiments_summary: {e}")
            return []


    def get_recent_data_for_graph(self):
        """
        Fetches all available experiment data for the time series graph.

        Returns:
            pd.DataFrame: DataFrame with columns: _time, _measurement, and variables of interest.
        """
        try:
            flux_query = f"""
            from(bucket: "{self.buckets["RAW"]}")
            |> range(start: 0)  // Get all data from the beginning
            |> filter(fn: (r) => exists r["{str(INFLUXDB_BATCH_ID)}"])
            |> keep(columns: ["_time", "_value", "batch_id", "device_id", "observed_property"])
            |> group(columns: ["batch_id"])
            |> pivot(rowKey:["_time"], columnKey: ["observed_property"], valueColumn: "_value")
            """

            result = self.connector.query_api.query_data_frame(flux_query)

            if isinstance(result, list):
                if not result:
                    logger.info("No data found in the database.")
                    return pd.DataFrame()
                df = pd.concat(result, ignore_index=True)
            else:
                df = result

            if df.empty:
                logger.info("No data found in the database.")
                return pd.DataFrame()

            if "_time" not in df.columns or INFLUXDB_BATCH_ID not in df.columns:
                logger.warning("Required fields are missing.")
                return pd.DataFrame()
            return df

        except Exception as e:
            logger.error(f"get_recent_data_for_graph: {e}")
            return pd.DataFrame()
        
    from datetime import datetime, timezone

    def get_last_timestamp_for_experiment(self, experiment_id: str):
        """
        Return the last timestamp for a given experiment_id within the last 90 days.
        If no data is found, returns None.
        """
        try:
            query = f'''
            from(bucket: "{str(self.buckets["RAW"])}")
            |> range(start: 0)
            |> filter(fn: (r) => r["batch_id"] == "{experiment_id}")
            |> keep(columns: ["_time", "_value", "batch_id", "device_id", "observed_property"])
            |> sort(columns: ["_time"], desc: true)
            |> limit(n:1)
            |> pivot(rowKey:["_time"], columnKey: ["observed_property"], valueColumn: "_value")
            '''
            
            result = self.connector.query_api.query(query)

            for table in result:
                for record in table.records:
                    return record.get_time()  # datetime UTC
            return None

        except Exception as e:
            logger.error(f"Error getting last timestamp for {experiment_id}: {e}")
            return None
