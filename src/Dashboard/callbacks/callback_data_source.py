import dash
from dash import Input, Output, State, dcc, html, dash_table, MATCH
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from Dashboard.config import NAME_PROJECT,PROJECT_ID
from Dashboard.utils import model_information
from Dashboard.InfluxDb import influxdb_handler  # Retrieve the created instance
from Dashboard.utils.utils_data_source import get_variable_category, generate_projects_details_view  # Load the necessary utility functions for the callbacks
import plotly.express as px
import pandas as pd
import numpy as np
import logging
from datetime import date

logger = logging.getLogger(__name__)


@dash.callback(
    Output("experiment-dropdown", "value"),
    Output("store-selected-state", "data"),
    Input("experiment-dropdown", "value"),   # Dispara el callback
    State("store-selected-state", "data"),   # Solo se lee, no dispara
    prevent_initial_call=True
)
def sync_dropdown_and_store(dropdown_value, store_data):
    # Caso 1: si el dropdown está vacío pero hay algo guardado en el store → restaurar
    if (not dropdown_value) and store_data and "selected_experiment" in store_data:
        return store_data["selected_experiment"], store_data

    # Caso 2: si el usuario selecciona algo nuevo → guardar en el store
    if dropdown_value:
        store_data = store_data or {}
        store_data["selected_experiment"] = dropdown_value
        return dropdown_value, store_data

    # Si nada aplica → no cambiar nada
    return dash.no_update, dash.no_update

    
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
        print(duration)
        if duration >= 24:
            return f"Experiment Duration: {round(duration / 24)} days"
        return f"Experiment Duration: {round(duration)} hours"
    except Exception as e:
        print(f"Error fetching experiment duration: {e}")
        return "Experiment Duration: Error"

@dash.callback(
    [Output("data-table", "data"),
     Output("table-title-container", "children")],
    [Input("experiment-dropdown", "value")]
)
def update_table_data(experiment_id):
    """
    Updates the table and its title with data from the selected experiment.
    """
    if not experiment_id:
        raise PreventUpdate

    try:
        raw_data = influxdb_handler.get_data_for_table(experiment_id)
        
        processed_data = []
        for row in raw_data:
            if "Name" in row and row["Name"]:
                row["Type"] = get_variable_category(row["Name"])
            else:
                row["Type"] = "Unknown"
            processed_data.append(row)
        
        title = html.H5(f"Statistical summary of the variables from the chosen experiment: {experiment_id}")
        return processed_data, title

    except Exception as e:
        print(f"Error updating table data: {e}")
        return [], html.H4("Error loading experiment data")

@dash.callback(
    [Output("offline-link", "disabled"),
     Output("online-link", "disabled"),
     Output("store-selected-state", "data",allow_duplicate=True)],
    Input("experiment-dropdown", "value"),
    State("store-selected-state", "data"),
    prevent_initial_call=True
)
def toggle_links(experiment_selected, store_data):
    """
    Enable or disable the 'Online' and 'Offline' links based on whether the selected experiment
    has received data within the last 5 minutes. Update only the 'online' key in dcc.Store.

    Args:
        experiment_selected (str): The selected experiment ID from the dropdown.
        store_data (dict): Current data in the store.

    Returns:
        (bool, bool, dict): States for offline-link, online-link and updated store data.
    """
    # Si no había nada en el store, inicializarlo como diccionario vacío
    if store_data is None:
        store_data = {}

    if not experiment_selected:
        store_data["online"] = False
        return False, True, store_data

    try:
        df = influxdb_handler.get_data_experiment_id(experiment_selected, minutes=5)

        if df.shape[0] > 0:
            store_data["online"] = True
            return True, False, store_data

        store_data["online"] = False
        return False, True, store_data

    except Exception as e:
        print(f"[Error] toggle_links: {e}")
        store_data["online"] = False
        return False, True, store_data

@dash.callback(
    Output('project-details', 'children'),
    Output("project-name", "children"),
    Input("experiment-dropdown", "value")
)
def display_project_details(value):
    """
    Update project information and name based on the selected experiment.

    This callback is triggered when the user selects a value from the
    `experiment-dropdown`. It retrieves the project details using
    `model_information.project_details()`, constructs a formatted display
    for the project information, and updates both the project detail
    section and the project name header.

    Parameters
    ----------
    value : str
        The selected experiment identifier from the dropdown input.

    Returns
    -------
    tuple
        A tuple containing:
        - dash.html.Component : A formatted HTML view with project details.
        - str : A string representing the project name header.
    """
    data_info = model_information.project_details()
    name = f"Project name: {NAME_PROJECT}"
    if data_info:
        data = {
            "description": data_info.get('description', {})
        }
        return generate_projects_details_view(data), name
    else:
        return html.P("Information regarding this project is not found"), name

@dash.callback(
    Output("table-experiments-online", "data"),
    Output("experiment-message", "children"),
    Output("experiment-message", "color"),
    Output("experiment-message", "is_open"),
    Input("interval-component", "n_intervals"),
    Input("time-unit-selector", "value"),
    Input("time-value-selector", "value")
)
def update_online_experiments(n_intervals, selected_unit, selected_value):
    """
    Periodically updates the experiment table with online data, applying time filtering
    based on the selected unit and value.

    Args:
        n_intervals (int): Number of triggered intervals (from dcc.Interval).
        selected_unit (str): Time unit selected by the user (seconds, minutes, etc.).
        selected_value (int): Time range value selected by the user.

    Returns:
        list: List of dictionaries with experiment data filtered by the selected time window.
    """
    try:
        if not selected_unit or not selected_value:
            return [], "Please select a valid time range.", "warning", True
        
        summary = influxdb_handler.get_online_experiments_summary(
            time_unit=selected_unit,
            time_value=selected_value
        )

        if not summary:
            return [], "No recent data found for the selected time range.", "info", True


        # Si la función devuelve un solo dict, lo empaquetas como lista
        if isinstance(summary, dict):
            return [summary], "", "info", False  # Hide the alert when there is data
        
        if isinstance(summary, list) and summary:
            return summary, "", "info", False  # Hide the alert when there is data

        # Fallback if summary is a list but empty (precaución extra)
        return [], "No recent data found for the selected time range.", "info", True

    except Exception as e:
        print(f"[Error] update_online_experiments: {e}")
        return [], "An error occurred while fetching the data.", "danger", True



@dash.callback(
    Output("line-experiments", "figure"),
    Input('ds-date-picker-range', 'start_date'),
    Input('ds-date-picker-range', 'end_date'),
    Input("field-selector", "value"),
)
def update_timeseries_data_count(start_date, end_date, selected_field):
    """Updates the time series chart showing valid data point counts per interval."""
    print("selected_field:", selected_field)
    try:
        if not start_date or not end_date or not selected_field:
            return go.Figure()

        df = influxdb_handler.get_recent_data_for_graph()
        if df.empty or "_time" not in df.columns:
            return go.Figure()

        df["_time"] = pd.to_datetime(df["_time"])
        mask = (df["_time"] >= start_date) & (df["_time"] <= end_date)
        df = df.loc[mask]
        if df.empty:
            return go.Figure()

        start, end = pd.to_datetime(start_date), pd.to_datetime(end_date)
        diff_days = (end - start).days

        # Seleccionar frecuencia automática
        if diff_days <= 1:
            freq = "H"
        elif diff_days <= 7:
            freq = "3H"
        elif diff_days <= 30:
            freq = "D"
        elif diff_days <= 180:
            freq = "W"
        else:
            freq = "M"

        print(f"Resample frequency: {freq}, Range: {diff_days} days")

        results = []

        for exp_id in df["_measurement"].unique():
            df_exp = df[df["_measurement"] == exp_id].copy()
            df_exp.set_index("_time", inplace=True)
            df_exp = df_exp.sort_index()

            # Contar registros por frecuencia
            if selected_field == "all":
                data_count = df_exp.resample(freq).count().sum(axis=1)
            else:
                if selected_field not in df_exp.columns:
                    continue
                data_count = df_exp[selected_field].resample(freq).count()

            partial_df = pd.DataFrame({
                "_time": data_count.index,
                "Experiment ID": exp_id,
                "Data Count": data_count.values
            })
            results.append(partial_df)

        if not results:
            return go.Figure()

        final_df = pd.concat(results, ignore_index=True)

        fig = px.bar(
            final_df,
            x="_time",
            y="Data Count",
            color="Experiment ID",
            title=f"Data Count {start_date} - {end_date} ({selected_field})"
        )

        fig.update_layout(
            barmode="group",
            margin={"l": 20, "r": 20, "t": 50, "b": 20},
            xaxis_title="Time",
            yaxis_title="Data count"
        )

        return fig

    except Exception as e:
        print(f"[ERROR] update_timeseries_data_count: {e}")
        return go.Figure()


@dash.callback(
    Output("field-selector", "options"),
    Input("interval-component", "n_intervals"),
)
def load_field_options(n_intervals):
    """
    Dynamically loads available fields from InfluxDB for the dropdown.
    """
    try:
        df = influxdb_handler.get_recent_data_for_graph()

        if df.empty:
            return [{"label": "All fields", "value": "all"}]

        excluded = ["_time", "_measurement", "experiment_id", "_start", "_stop","result","table","Batch"]
        valid_fields = [col for col in df.columns if col not in excluded]

        options = [{"label": "All fields", "value": "all"}]
        options += [{"label": field.capitalize(), "value": field} for field in valid_fields]

        return options

    except Exception as e:
        print(f"[ERROR] load_field_options: {e}")
        return [{"label": "All fields", "value": "all"}]

@dash.callback(
    Output('output-container-date-picker-range', 'children'),
    Input('ds-date-picker-range', 'start_date'),
    Input('ds-date-picker-range', 'end_date'))
def update_output(start_date, end_date):
    string_prefix = 'You have selected: '
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        start_date_string = start_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        end_date_string = end_date_object.strftime('%B %d, %Y')
        string_prefix = string_prefix + 'End Date: ' + end_date_string
    if len(string_prefix) == len('You have selected: '):
        return 'Select a date to see it displayed here'
    else:
        return string_prefix


