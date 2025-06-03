import dash
from dash import Input, Output, State, dcc, html, dash_table, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from utils import model_information
from InfluxDb import influxdb_handler  # Retrieve the created instance
from utils.utils_data_source import get_variable_category, generate_projects_details_view  # Load the necessary utility functions for the callbacks
import plotly.express as px
import pandas as pd


@dash.callback(
    Output("store-selected-state", "data"),
    Input("experiment-dropdown", "value")
)
def store_selected_experiment(experiment_id):
    return {"selected_experiment": experiment_id} if experiment_id else {}
        
@dash.callback(
    Output({"type": "experiment-dropdown", "index": MATCH}, "value"),
    Output({"type": "store-selected-state", "index": MATCH}, "data"),  # Added MATCH
    State({"type": "experiment-dropdown", "index": MATCH}, "value"),
    Input({"type": "store-selected-state", "index": MATCH}, "data"),  # Must also use MATCH
    prevent_initial_call=True
)
def sync_experiment_selection(experiment_id, store_data):
    # If there is a stored value and it has not been changed in the dropdown, restore it
    if store_data and "selected_experiment" in store_data and experiment_id is None:
        return store_data["selected_experiment"], store_data

    # If the user selects something new, store it
    return experiment_id, {"selected_experiment": experiment_id} if experiment_id else {}
    
@dash.callback(
    [Output("bucket-dropdown", "options"),
    Output("experiment-dropdown", "options")],
    [Input("bucket-dropdown", "value")]
)
def update_dropdowns(selected_bucket):
    """Updates the dropdown options based on ONLINE/OFFLINE state."""
    try:
        bucket_options = [{"label": b, "value": b} for b in influxdb_handler.get_buckets()]
        experiment_options = []
        if selected_bucket:
            # Solo obtener experimentos con datos en los últimos 5 minutos
            #exp_recent = influxdb_handler.get_recent_experiment_ids(selected_bucket, minutes=5)
            # Obtener todos los experimentos sin importar la fecha
            exp_all = influxdb_handler.get_distinct_experiment_ids(selected_bucket)
            print("Experiments ID: ",exp_all)
            experiment_options = [{"label": exp, "value": exp} for exp in exp_all]

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
    """Updates the bar chart with experiment data."""
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
    """Updates the table with data from the selected experiment."""
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
    Input("experiment-dropdown", "value")
)
def toggle_links(experiment_selected):
    """
    Enable or disable the 'Online' and 'Offline' links based on whether the selected experiment
    has received data within the last 5 minutes.

    Args:
        experiment_selected (str): The selected experiment ID from the dropdown.

    Returns:
        (bool, bool): Tuple to set the 'disabled' state of 'offline-link' and 'online-link'.
    """
    if not experiment_selected:
        # No experiment selected; enable offline by default
        return False, True

    try:
        df = influxdb_handler.get_data_experiment_id(experiment_selected, minutes=5)

        if df.shape[0] > 0:
            # Recent data found → enable 'online', disable 'offline'
            return True, False

        # No recent data → enable 'offline', disable 'online'
        return False, True

    except Exception as e:
        print(f"[Error] toggle_links: {e}")
        # In case of error, enable offline by default
        return False, True

@dash.callback(
            Output('project-details', 'children'),
            Input("experiment-dropdown", "value")
        )
def display_project_details(value):
    data_info = model_information.project_details()

    if data_info:
                
        data = {
            "description": data_info.get('description', {})
            }
        return generate_projects_details_view(data)
    else:
        return html.P("The information project not found.")
    
@dash.callback(
    Output('histogram_experiments', 'figure'),
    Output('prev_experiment_ids', 'data'),
    Input('interval-component', 'n_intervals'),
    Input('bucket-dropdown', 'value'),
    State('prev_experiment_ids', 'data'),
)
def update_histogram(n, bucket, prev_data):
    if bucket is None:
        return px.bar(title="Please select a bucket to display data"), prev_data

    count_df = influxdb_handler.get_count_data_experiment_ids(bucket)

    if count_df.empty:
        return px.bar(title="No experiments found for the selected bucket"), prev_data

    # Convert previous data to dict if exists, otherwise empty
    prev_data = prev_data or {}
    
    current_data = dict(zip(count_df['experiment_id'], count_df['num_points']))
    changed_ids = []

    for eid, count in current_data.items():
        if eid not in prev_data or count > prev_data[eid]:
            changed_ids.append(eid)

    # Color map: changed = naranja, igual = azul
    color_map = {
        eid: '#FF5733' if eid in changed_ids else '#4682B4'
        for eid in current_data.keys()
    }

    fig = px.bar(
        count_df,
        x='experiment_id',
        y='num_points',
        labels={'experiment_id': 'Experiment ID', 'num_points': 'Number of Points'},
        title=f'Number of Data Points per Experiment ID in Bucket "{bucket}"',
        color='experiment_id',
        color_discrete_map=color_map
    )
    fig.update_layout(showlegend=False)

    return fig, current_data  # <-- Guarda el nuevo estado con conteo
