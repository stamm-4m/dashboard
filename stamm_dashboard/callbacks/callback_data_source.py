import logging

import dash
import plotly.graph_objs as go
from dash import Input, Output, State, MATCH
from dash.exceptions import PreventUpdate
from ..utils.utils_data_source import get_variable_category  # se carganlas fuciones utils necesarias para los callback

from ..InfluxDb import influxdb_handler  # recuperamos la instancia creada

logging.debug("Loading callbacks for data source")

@dash.callback(
    Output("store-selected-state", "data"),
    Input("experiment-dropdown", "value")
)
def store_selected_experiment(experiment_id):
    return {"selected_experiment": experiment_id} if experiment_id else {}
        
@dash.callback(
    Output({"type": "experiment-dropdown", "index": MATCH}, "value"),
    Output({"type": "store-selected-state", "index": MATCH}, "data"),  # Agregado MATCH
    State({"type": "experiment-dropdown", "index": MATCH}, "value"),
    Input({"type": "store-selected-state", "index": MATCH}, "data"),  # También debe usar MATCH
    prevent_initial_call=True
)
def sync_experiment_selection(experiment_id, store_data):
    # Si hay un valor almacenado y no se ha cambiado en el dropdown, lo restauramos
    if store_data and "selected_experiment" in store_data and experiment_id is None:
        return store_data["selected_experiment"], store_data

    # Si el usuario seleccionó algo nuevo, lo almacenamos
    return experiment_id, {"selected_experiment": experiment_id} if experiment_id else {}
    
@dash.callback(
    [Output("bucket-dropdown", "options"),
    Output("experiment-dropdown", "options")],
    [Input("real-time-radio", "value"),
    Input("bucket-dropdown", "value")]
)
def update_dropdowns(selected_option, selected_bucket):
    """Actualiza las opciones de los dropdowns en función del estado ONLINE/OFFLINE."""
    try:
                if selected_option == "ON":
                    bucket_options = [{"label": "STAMM_DATA", "value": "STAMM_DATA"}]
                    experiment_options = [{"label": "4.0", "value": "4.0"}]
                    return bucket_options, experiment_options
                else:
                    bucket_options = [{"label": b, "value": b} for b in influxdb_handler.get_buckets()]

                experiment_options = []
                if selected_bucket:
                    experiments = influxdb_handler.get_distinct_experiment_ids(selected_bucket)
                    print(experiments)
                    experiment_options = [{"label": exp, "value": exp} for exp in experiments]

                return bucket_options, experiment_options
    except Exception as e:
        print(f"Error updating dropdowns: {e}")
        return [], []

@dash.callback(
    Output("duration-text", "children"),
    Input("experiment-dropdown", "value")
)
def update_duration_text(experiment_id):
            """Updates the experiment duration text based on the selected experiment."""
            if not experiment_id:
                return "Experiment Duration: N/A"
            
            try:
                duration = influxdb_handler.get_experiment_duration(experiment_id)
                if duration >= 24:
                    return f"Experiment Duration: {round(duration / 24)} days"
                return f"Experiment Duration: {round(duration)} hours"
            except Exception as e:
                print(f"Error fetching experiment duration: {e}")
                return "Experiment Duration: Error"

@dash.callback(
    Output("bar-chart", "figure"),
    [Input("bucket-dropdown", "value"),
    Input("experiment-dropdown", "value")]
)
def update_bar_chart(bucket, experiment_id):
            """Actualiza el gráfico de barras con datos del experimento."""
            if not bucket or not experiment_id:
                raise PreventUpdate

            try:
                category_counts = influxdb_handler.get_category_counts(bucket, experiment_id)
                return go.Figure(data=[go.Bar(x=list(category_counts.keys()), y=list(category_counts.values()))])
            except Exception as e:
                print(f"Error updating bar chart: {e}")
                return go.Figure()

@dash.callback(
    Output("data-table", "data"),
    [Input("bucket-dropdown", "value"),
    Input("experiment-dropdown", "value")]
)
def update_table_data(bucket, experiment_id):
            """Actualiza la tabla con datos del experimento seleccionado."""
            if not bucket or not experiment_id:
                raise PreventUpdate

            try:
                raw_data = influxdb_handler.get_data_for_table(bucket, experiment_id)
                
                # Ensure variable names exist and categorize them
                processed_data = []
                for row in raw_data:
                    if "Name" in row and row["Name"]:
                        row["Type"] = get_variable_category(row["Name"])
                    else:
                        row["Type"] = "Unknown"
                    processed_data.append(row)
                
                return processed_data
            except Exception as e:
                print(f"Error updating table data: {e}")
                return []

@dash.callback(
    [Output("offline-link", "disabled"),
    Output("online-link", "disabled")],
    [Input("real-time-radio", "value")]
)
def toggle_links(real_time_value):
            if real_time_value == "ON":
                return True, False
            return False, True
       

