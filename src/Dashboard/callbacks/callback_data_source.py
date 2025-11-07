import dash
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from Dashboard.config import NAME_PROJECT
from Dashboard.utils import model_information
from Dashboard.InfluxDb import influxdb_handler  # Retrieve the created instance
from Dashboard.utils.utils_data_source import get_variable_category, generate_projects_details_view  # Load the necessary utility functions for the callbacks
import plotly.express as px
import pandas as pd
import logging
import humanize
from datetime import date, datetime, timezone

logger = logging.getLogger(__name__)

@dash.callback(
    Output("experiment-dropdown", "value"),
    Output("store-selected-state", "data"),
    Input("experiment-dropdown", "value"),   
    State("store-selected-state", "data"),
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
    """Load experiment options ordered by most recent timestamp first."""
    try:
        exp_all = influxdb_handler.get_distinct_experiment_ids()
        logger.debug(f"Experiments ID: {exp_all}")

        now = datetime.now(timezone.utc)
        experiment_data = []

        # Get timestamps and store them for sorting
        for exp in exp_all:
            last_ts = influxdb_handler.get_last_timestamp_for_experiment(exp)
            experiment_data.append((exp, last_ts))

        # Sort by timestamp (most recent first)
        experiment_data.sort(key=lambda x: x[1] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        # Build dropdown options
        experiment_options = []
        for exp, last_ts in experiment_data:
            if last_ts:
                diff = now - last_ts
                logger.debug(f"diff for {exp}: {diff}")

                if diff.days > 90:
                    label = f"{exp} - more than 3 months ago"
                else:
                    diff_str = humanize.naturaltime(diff)
                    label = f"{exp} - last data {diff_str}"
            else:
                label = f"{exp} - more than 3 months ago"

            experiment_options.append({"label": label, "value": exp})

        return [experiment_options]

    except Exception as e:
        logger.error(f"Error updating dropdowns: {e}")
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
        logger.debug(f"duration: {duration}")
        if duration >= 24:
            return f"Experiment Duration: {round(duration / 24)} days"
        return f"Experiment Duration: {round(duration)} hours"
    except Exception as e:
        logger.error(f"Error fetching experiment duration: {e}")
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
        logger.error(f"Error updating table data: {e}")
        return [], html.H4("Error loading experiment data")

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

    if data_info:
        name = f"Project name: {data_info.get('project_name',{})}"
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
    Periodically updates the experiment table with online data, applying time filtering.
    Avoids redundant updates when no data is found.
    """
    try:
        if not selected_unit or not selected_value:
            logger.debug("not selected_unit or not selected_value")
            return dash.no_update, "No selected unit or selected value.", "info", True
        summary = influxdb_handler.get_online_experiments_summary(
            time_unit=selected_unit,
            time_value=selected_value
        )

        if not summary:
            return dash.no_update, "No recent data found for the selected time range.", "info", True

        # Si hay datos, los mostramos y ocultamos el mensaje
        if isinstance(summary, dict):
            return [summary], "", "info", False
        elif isinstance(summary, list) and summary:
            return summary, "", "info", False


    except Exception as e:
        logger.error(f"update_online_experiments: {e}")
        return [], "An error occurred while fetching the data.", "danger", True



@dash.callback(
    Output("line-experiments", "figure"),
    Input('ds-date-picker-range', 'start_date'),
    Input('ds-date-picker-range', 'end_date'),
    Input("field-selector", "value"),
)
def update_timeseries_data_count(start_date, end_date, selected_field):
    """Updates the time series chart showing valid data point counts per interval."""
    logger.debug(f"selected_field:{selected_field}")
    try:
        if not start_date or not end_date or not selected_field:
            logger.debug(f"not start_date or not end_date or not selected_field")
            return go.Figure()

        df = influxdb_handler.get_recent_data_for_graph()
        if df.empty or "_time" not in df.columns:
            logger.debug(f"empty dataframe or column _time no found")
            return go.Figure()
        logger.debug(f"df:\n{df}")
        df["_time"] = pd.to_datetime(df["_time"])
        mask = (df["_time"] >= start_date) & (df["_time"] <= end_date)
        df = df.loc[mask]
        if df.empty:
            logger.debug(f" empty dataframe")
            return go.Figure()

        start, end = pd.to_datetime(start_date), pd.to_datetime(end_date)
        diff_days = (end - start).days

        # Seleccionar frecuencia automática
        if diff_days <= 1:
            freq = "h"
        elif diff_days <= 7:
            freq = "3h"
        elif diff_days <= 30:
            freq = "D"
        elif diff_days <= 180:
            freq = "W"
        else:
            freq = "M"

        logger.debug(f"Resample frequency: {freq}, Range: {diff_days} days")

        results = []

        for exp_id in df["batch_id"].unique():
            df_exp = df[df["batch_id"] == exp_id].copy()
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
            logger.debug(f"not results")
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
        logger.error(f"update_timeseries_data_count: {e}")
        return go.Figure()


@dash.callback(
    Output("field-selector", "options"),
    Input("interval-component", "n_intervals"),
    State("field-selector", "options"),
    prevent_initial_call=True
)
def load_field_options(interval, current_options):
    """
    Updates the field selector options based on recent data from InfluxDB.

    Args:
        interval (int): The number of intervals passed since the app started.
        current_options (list): The current options available in the field selector.

    Returns:
        list: Updated list of field options for the dropdown.
    """
    try:
        df = influxdb_handler.get_recent_data_for_graph()
        if df.empty:
            return current_options or [{"label": "All fields", "value": "all"}]

        excluded = ["_time", "experiment_time", "result", "table", "batch_id"]
        valid_fields = [col for col in df.columns if col not in excluded]

        new_options = [{"label": "All fields", "value": "all"}]
        new_options += [{"label": field.capitalize(), "value": field} for field in valid_fields]

        # ✅ Prevents refresh if there are no real changes
        if new_options == current_options:
            return dash.no_update

        logger.debug(f"Updated field options ({len(valid_fields)})")
        return new_options

    except Exception as e:
        logger.error(f"load_field_options: {e}")
        return current_options or [{"label": "All fields", "value": "all"}]


@dash.callback(
    Output('output-container-date-picker-range', 'children'),
    Input('ds-date-picker-range', 'start_date'),
    Input('ds-date-picker-range', 'end_date')
)
def update_output(start_date, end_date):
    """
    Updates the displayed text based on the selected date range.

    Args:
        start_date (str): Start date in ISO format (YYYY-MM-DD).
        end_date (str): End date in ISO format (YYYY-MM-DD).

    Returns:
        str: Text describing the selected date range.
    """
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

