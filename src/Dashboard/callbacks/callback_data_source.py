import dash
from dash import Input, Output, State, dcc, html, dash_table, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from Dashboard.utils import model_information
from Dashboard.InfluxDb import influxdb_handler  # Retrieve the created instance
from Dashboard.utils.utils_data_source import get_variable_category, generate_projects_details_view  # Load the necessary utility functions for the callbacks
import plotly.express as px
import pandas as pd
import numpy as np



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
    [Output("experiment-dropdown", "options")],
    [Input("url", "pathname")]
)
def update_dropdowns(pathname):
    """Load experiment options when page loads or URL changes."""
    try:
        exp_all = influxdb_handler.get_distinct_experiment_ids()
        print("Experiments ID: ", exp_all)

        experiment_options = [{"label": exp, "value": exp} for exp in exp_all]

        return [experiment_options]  # Siempre lista dentro de otra lista
    except Exception as e:
        print(f"Error updating dropdowns: {e}")
        return [[]]


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
    [Input("experiment-dropdown", "value")]
)
def update_bar_chart(experiment_id):
    """Updates the bar chart with experiment data."""
    if not experiment_id:
        raise PreventUpdate

    try:
        category_counts = influxdb_handler.get_category_counts(experiment_id)
        fig =  go.Figure(
            data=[go.Bar(x=list(category_counts.keys()), y=list(category_counts.values()))]
            )
        fig.update_layout(
            title={
            'text': f'Number of variables by type in Experiment {experiment_id}',
            'x': 0.5  # Centra el título horizontalmente
    }
        )
        return fig
    except Exception as e:
        print(f"Error updating bar chart: {e}")
        return go.Figure()

@dash.callback(
    Output("data-table", "data"),
    [Input("experiment-dropdown", "value")]
)
def update_table_data(experiment_id):
    """Updates the table with data from the selected experiment."""
    if not experiment_id:
        raise PreventUpdate

    try:
        raw_data = influxdb_handler.get_data_for_table(experiment_id)
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
    State('prev_experiment_ids', 'data'),
)
def update_histogram(n, prev_data):
    
    count_df = influxdb_handler.get_count_data_experiment_ids()

    if count_df.empty:
        return px.bar(title="No experiments found for the  bucket"), prev_data

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
        color='experiment_id',
        color_discrete_map=color_map
    )
    fig.update_layout(
        title={
            'text': 'Number of data points per experiment',
            'x': 0.5  # Centrar el título
        }
    )
    fig.update_layout(showlegend=False)

    return fig, current_data  # <-- Guarda el nuevo estado con conteo

@dash.callback(
    Output("table-experiments-online", "data"),
    Input("interval-component", "n_intervals")
)
def update_online_experiments(n_intervals):
    try:
        summary = influxdb_handler.get_online_experiments_summary()

        # Si la función devuelve un solo dict, lo empaquetas como lista
        if isinstance(summary, dict):
            return [summary]

        # Si ya es lista, la devuelves tal cual
        return summary if summary else []

    except Exception as e:
        print(f"[Error] update_online_experiments: {e}")
        return []


@dash.callback(
    Output("table-experiments-previous", "data"),
    Input("interval-component", "n_intervals")
)
def update_previous_experiments(n_intervals):
    try:
        results = influxdb_handler.get_previous_experiments_summary()

        print("Resultados previos limpios:", results)

        if not results:
            return []

        # Casteo preventivo por si quedó algo en formato raro
        for item in results:
            if isinstance(item["Temperature"], (np.floating, np.float64)):
                item["Temperature"] = float(item["Temperature"])

        return results

    except Exception as e:
        print(f"[Error] update_previous_experiments: {e}")
        return []
