import os
from dash import Input, Output, State, dcc, ALL, ctx, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash
import pandas as pd
import re
import plotly.graph_objects as go
from Dashboard.InfluxDb import influxdb_handler # retrieve the created instance
import io
import sqlite3
from Dashboard.utils import sqlite_handler
import plotly.express as px
from Dashboard.config import DB_ENGINE, BASE_URL_API, INFLUXDB_BUCKET_RAW
import logging
from Dashboard.utils.utils_model_information import get_model_information

logger = logging.getLogger(__name__) 

dfc = pd.DataFrame()
# Set model pre-selected
@dash.callback(
    Output("model-selector-maintenance", "value"),
    Input("model-data-store", "data")
)
def update_model_display(data):
    """
    Updates the model selector field with the currently selected model.

    This callback automatically sets the model name in the model selector 
    based on the data stored in "model-data-store". If no model is found, 
    a default message is displayed.

    Args:
        data (dict): Stored model information containing at least the key 'model_name'.

    Returns:
        str: The name of the selected model, or 'No selected model' if none is available.
    """
    # Check if the model data exists and contains a valid model name
    if not data or "model_name" not in data or not data["model_name"]:
        logger.warning("No model name found in data.")
        return "No selected model"

    # Return the model name as a formatted string
    return f"{data['model_name']}"

@dash.callback(
    Output('model-selector-maintenance', 'options'),
    Input('model-selector-maintenance', 'n_clicks'),
    State("store-selected-state", "data"),
)
def update_model_options(n_clicks, store_data):
    """
    Updates the list of available models in the model selector.

    This callback reloads the models every time the model selector is clicked 
    to ensure the options list is always up to date.

    Args:
        n_clicks (int): The number of times the model selector has been clicked.

    Returns:
        list: A list of dictionaries representing model options for the selector.
    """
    # Reload all available models
    reload_models(store_data.get("selected_project"))  # Pass the project
    model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
    # Retrieve and return updated model names for the dropdown options
    return model_information.get_model_name_options()

# Calls the function again to read  'Models
def reload_models(project_id):
    model_information = get_model_information(project_id)
    model_information.configurations = []
    model_information.load_all_models()

# Show selected experiment ID
@dash.callback(
    Output("experiment-id-display-maintenence", "children"),
    Input("store-selected-state", "data"),
)
def update_experiment_display(data):
    """
    Displays the selected experiment ID in the interface.

    This callback retrieves the selected experiment ID from the 
    'store-selected-state' data and shows it on the screen. 
    If no experiment is selected, it displays a default message.

    Args:
        data (dict): A dictionary containing the current selected experiment information.

    Returns:
        str: The selected experiment ID or a default message if none is selected.
    """
    # Check if data exists and contains a valid experiment ID
    if not data or "selected_experiment" not in data or not data["selected_experiment"]:
        return "No experiment ID Selected"

    # Display the selected experiment ID
    return f"{data['selected_experiment']}"
 

# Confirm maintenance
@dash.callback(
    Output("maintain-reason", "value"),
    Input("confirm-maintain", "n_clicks"),
    State("maintain-reason", "value"),
    prevent_initial_call=True
)
def confirm_maintenance(n_clicks, reason):
    """
    Confirms the maintenance action and logs the provided reason.

    This callback is triggered when the user clicks the confirm button. 
    If a maintenance reason is provided, it prints a confirmation message 
    and clears the input field. Otherwise, it keeps the current value.

    Args:
        n_clicks (int): Number of times the confirm button has been clicked.
        reason (str): The maintenance reason entered by the user.

    Returns:
        str or dash.no_update: Returns an empty string to clear the input field 
        if a reason is provided, otherwise keeps the current value.
    """
    # Check if a maintenance reason was provided
    if reason:
        print(f"Maintenance confirmed with reason: {reason}")
        # Clear the input field after confirmation
        return ""
    
    # Keep the current value if no reason is provided
    return dash.no_update

# Function to update the types of model inputs
@dash.callback(
    Output('type-selector-maintenance', 'options'),
    Input('model-selector-maintenance', 'value'),
    State("store-selected-state", "data"),
    prevent_initial_call=True
)
def update_model_types_maintenance(name, store_data):
    """
    Updates the available model type options based on the selected model name.

    This callback retrieves the list of model types associated with the 
    selected model and updates the dropdown options dynamically.

    Args:
        name (str): The name of the selected model.

    Returns:
        list: A list of available model type options. Returns an empty list if 
        no types are found for the given model.
    """
    # Retrieve unique model types based on the selected model name
    model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
    types_variable = model_information.get_unique_types_models(name)
    
    # Log a debug message and return an empty list if no types are found
    if types_variable is None:
        logger.debug(f"types_variable {types_variable} for {name}")
        return []
    
    # Return the available model type options
    return types_variable

@dash.callback(
    Output('name-selector-maintenance', 'options'),
    Input('type-selector-maintenance', 'value'),
    Input('model-selector-maintenance', 'value'),
    State("store-selected-state", "data"),
)
def update_name_selector(selected_category, model_name, store_data):
    """
    Updates the options for the 'name-selector-maintenance' dropdown 
    based on the selected category and model name.

    This callback retrieves the model names associated with the selected 
    category and model, dynamically populating the dropdown options.

    Args:
        selected_category (str): The category selected in the 'type-selector-maintenance' dropdown.
        model_name (str): The name of the currently selected model.

    Returns:
        list: A list of dictionaries containing the available name options 
        for the 'name-selector-maintenance' dropdown. Returns an empty list 
        if no category is selected.
    """
    if selected_category:
        # Retrieve names that correspond to the selected category and model
        model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
        logger.debug(f"name_variable: {model_information.get_names_by_category(selected_category, model_name)}")
        return model_information.get_names_by_category(selected_category, model_name)
    else:
        # Return an empty list if no category is selected
        return []

@dash.callback(
    Output("filter-name-selector", "options"),
    Input("prediction-table", "columns"),
    prevent_initial_call=True
)
def update_filter_column_options(column_list):
    """
    Updates the options of the column selector dropdown for filtering.

    This callback dynamically generates the dropdown options based on 
    the columns available in the prediction DataTable. It excludes 
    non-filterable columns such as 'Report', 'raw_time', and 'raw_prediction'.

    Args:
        column_list (list): List of column metadata dictionaries from the DataTable.
            Each dictionary should contain 'name' and 'id' keys.

    Returns:
        list: A list of dictionaries representing the dropdown options.
              Each dictionary contains 'label' and 'value' keys.
    """
    if not column_list:
        raise PreventUpdate

    # Build dropdown options excluding non-filterable columns
    return [
        {"label": col["name"], "value": col["id"]}
        for col in column_list
        if isinstance(col, dict)
        and "name" in col
        and "id" in col
        and col["id"] not in ["Report", "raw_time", "raw_prediction"]
    ]

@dash.callback(
    Output("prediction-table", "data", allow_duplicate=True),
    Input("filter-name-selector", "value"),
    Input("filter-value-input", "value"),
    State("prediction-table-store", "data"),
    prevent_initial_call=True
)
def filter_table(selected_column, value_filter, original_data):
    """
    Filters the DataTable data based on the selected column and user-provided value.

    This callback allows both numeric and text-based filtering:
    - Numeric filters can use comparison operators (e.g., "> 5", "<= 10").
    - Text filters perform partial string matching (useful for timestamps or text fields).

    Args:
        selected_column (str): The column ID selected for filtering.
        value_filter (str): The value or condition used to filter the selected column.
                            Supports numeric conditions (e.g., "> 5") or partial strings.
        original_data (list[dict]): The original unfiltered data stored in memory.

    Returns:
        list[dict]: The filtered subset of the original data.
    """
    if not original_data or not selected_column:
        raise PreventUpdate

    filtered = original_data

    if not value_filter:
        return filtered

    value_filter = value_filter.strip()
    op_match = re.match(r"([<>]=?|=)\s*(-?\d+(\.\d+)?)", value_filter)

    if op_match:
        # Numeric filtering (e.g., "> 2.5")
        op, val, _ = op_match.groups()
        val = float(val)

        def compare(v):
            """Compares numeric values based on the operator."""
            try:
                fv = float(v)
                if op == ">":
                    return fv > val
                elif op == "<":
                    return fv < val
                elif op == ">=":
                    return fv >= val
                elif op == "<=":
                    return fv <= val
                elif op == "=":
                    return fv == val
            except Exception:
                return False

        filtered = [row for row in filtered if compare(row.get(selected_column))]

    else:
        # Text-based partial match (e.g., filtering by datetime string)
        filtered = [
            row for row in filtered
            if selected_column in row and value_filter.lower() in str(row[selected_column]).lower()
        ]

    return filtered

def is_float(val):
    """
    Check if a given value can be converted to a float.

    Parameters:
    - val (any): The value to check.

    Returns:
    - bool: True if val can be converted to float, False otherwise.
    """
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False

# Callback to update the maintenance graph
@dash.callback(
    Output("maintenance-graph", "figure"),
    Output("prediction-table", "data"),  
    Output("prediction-table", "columns"),
    Output("prediction-table-store", "data"),
    Input("model-data-store", "data"),
    Input("store-selected-state", "data"),
    Input("time-window-slider", "value"),
    Input("add-variable-btn-maintenance", "n_clicks"),
    Input("selected-variables-maintenance", "data"),
    State("maintenance-graph", "figure"),
    prevent_initial_call=True
)
def update_graph_var_maintenance(data, data_exp, range_slider, n_clicks, selected_variables, current_figure):
    """
    Updates the maintenance graph and prediction table based on the selected experiment,
    model, and time window.

    This callback dynamically loads data from InfluxDB, filters it by time range,
    adds selected variables as traces, and updates both the plotly figure and
    the Dash DataTable.

    Args:
        data (dict): Model data from the store, including model name and ID.
        data_exp (dict): Experiment data containing the selected experiment ID.
        range_slider (list[int]): Indices representing the time window range.
        n_clicks (int): Number of clicks on the "add variable" button.
        selected_variables (list[dict]): List of selected variables with their names.
        current_figure (plotly.graph_objects.Figure): Current figure state before update.

    Returns:
        tuple:
            - go.Figure: Updated plotly figure with prediction and variable traces.
            - list[dict]: Data for the prediction table.
            - list[dict]: Column definitions for the prediction table.
            - list[dict]: Original table data stored for filtering.
    """
    global dfc

    # Check if an experiment has been selected
    if not data_exp or "selected_experiment" not in data_exp or not data_exp["selected_experiment"]:
        logger.warning("No experiment ID selected.")
        return go.Figure(), [], [], []
    
    # Load data from InfluxDB
    dfc = influxdb_handler.get_data_until_latest(data_exp["selected_experiment"])
    dfc["_time"] = pd.to_datetime(dfc["_time"], errors="coerce")

    # Filter data by time range
    timestamps = sorted(dfc["_time"].dropna().unique())
    start_time = timestamps[range_slider[0]]
    end_time = timestamps[range_slider[1]]
    dfc = dfc[(dfc["_time"] >= start_time) & (dfc["_time"] <= end_time)]
    logger.debug(f"Data: {data}")

    # Validate model data
    if not data or "model_name" not in data or not data["model_name"]:
        logger.warning("Model name not found.")
        return go.Figure(), [], [], []
    
    prediction_var = data["model_id"].lower()

    # === Prepare table section ===
    # Base columns
    columns_to_show = ["_time", prediction_var]

    # Add selected variables
    if selected_variables:
        for var_data in selected_variables:
            if isinstance(var_data, dict) and "variable_name" in var_data:
                var = var_data["variable_name"]
                if var in dfc.columns and var not in columns_to_show:
                    columns_to_show.append(var)

    # Filter DataFrame for table
    table_df = dfc[columns_to_show].dropna(subset=[prediction_var])

    # Store raw columns
    table_df["raw_time"] = table_df["_time"]
    if prediction_var in table_df.columns:
        table_df["raw_prediction"] = table_df[prediction_var]

    # Format timestamp and prediction values
    table_df["time_str"] = table_df["_time"].dt.strftime('%m/%d/%Y %H:%M:%S.%f')
    if prediction_var in table_df.columns:
        table_df[prediction_var + "_str"] = table_df[prediction_var].round(4)

    # Add "Report" column with markdown links
    table_df["Report"] = [
        f"[🚨 Report](#report-{i})" for i in range(len(table_df))
    ]
    
    # Prepare table for Dash: rename columns for display
    table_for_dash = table_df.drop(columns=["_time"]).rename(columns={"time_str": "_time"})
    table_for_dash = table_for_dash.drop(columns=[prediction_var]).rename(columns={prediction_var + "_str": prediction_var})

    # Convert table to dict and define visible columns
    table_data = table_for_dash.to_dict("records")
    table_columns = [
        {"name": col, "id": col} for col in table_for_dash.columns if col not in ["Report", "raw_time", "raw_prediction"]
    ]
    table_columns.append({
        "name": "Anomaly",
        "id": "Report",
        "presentation": "markdown"
    })
    hidden_columns = ["raw_time", "raw_prediction"]

    logger.debug(f"🔄 Callback executed - Clicks: {n_clicks}, Selected variables: {selected_variables}")

    if not selected_variables:
        logger.warning("⚠ No variables selected.")

    if dfc is None or "_time" not in dfc:
        logger.warning("⚠ No data or missing '_time' column.")
        return go.Figure(current_figure) if current_figure else go.Figure(), [], [], []

    # === Build graph ===
    df = pd.DataFrame(dfc)
    df["_time"] = pd.to_datetime(df["_time"], errors="coerce")

    fig = go.Figure()
    colors = px.colors.qualitative.Dark24
    existing_traces = set()

    # --- Add main prediction line on the primary Y-axis ---
    if prediction_var in df.columns:
        fig.add_trace(go.Scatter(
            x=df["_time"].astype(str),
            y=df[prediction_var],
            mode="lines",
            name=prediction_var,
            yaxis="y",
            line=dict(color="black", dash="solid"),
            hovertemplate="Time: %{x}<br>" + f"{prediction_var}: %{{y}}<extra></extra>"
        ))
        existing_traces.add(prediction_var)
        logger.debug(f"✅ Line '{prediction_var}' added to main Y-axis.")
    else:
        logger.warning(f"⚠ '{prediction_var}' not found in data.")

    # --- Add selected variable traces ---
    for i, var_data in enumerate(selected_variables):
        if not isinstance(var_data, dict) or "variable_name" not in var_data:
            logger.warning(f"⚠ Invalid format in selected_variables[{i}]: {var_data}")
            continue

        var = var_data["variable_name"]

        if var in df.columns and var not in existing_traces:
            color = colors[i % len(colors)]
            axis_id = f"y{i + 3}"  # Use y3, y4, etc. (y and y2 are reserved)

            fig.add_trace(go.Scatter(
                x=df["_time"].astype(str),
                y=df[var],
                mode="lines",
                name=var,
                yaxis=axis_id,
                line=dict(color=color),
                hovertemplate="Time: %{x}<br>" + f"{var}: %{{y}}<extra></extra>"
            ))
            existing_traces.add(var)
            logger.debug(f"✅ Variable '{var}' added to graph on axis {axis_id}.")
        else:
            logger.warning(f"⚠ '{var}' already plotted or not found.")

    # --- Define additional Y-axes for each selected variable ---
    extra_axes = {}
    for i, var_data in enumerate(selected_variables):
        axis_name = f"yaxis{i + 3}"  # yaxis3, yaxis4, ...
        side = "right"
        position = 1.0 - (i * 0.10) 

        extra_axes[axis_name] = dict(
            title=dict(
                text=var_data["variable_name"],
                font=dict(color=colors[i % len(colors)])
            ),
            tickfont=dict(color=colors[i % len(colors)]),
            anchor="x",
            overlaying="y",
            side=side,
            position=position,
            showgrid=False
        )

    # Update layout with dynamic axes
    fig.update_layout(
        xaxis=dict(title="Time", tickangle=-45, type="date"),
        yaxis=dict(
            showgrid=True,
            title=dict(
                text=prediction_var,
                font=dict(color="black")
            )
        ),
        yaxis2=dict(
            visible=False  # y2 is not used anymore
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        **extra_axes
    )
    
    return fig, table_data, table_columns, table_data

@dash.callback(
    Output("time-slider-labels", "children"),
    Output("time-window-slider", "max"),
    Input("store-selected-state", "data"),
    Input("time-window-slider", "value"),
    State("maintenance-graph", "figure")
)
def update_slider_labels(data,slider_range, figure):
    if not data or "selected_experiment" not in data or not data["selected_experiment"]:
        print("No experiment ID Selected")
        return "", 0

    dfc = influxdb_handler.get_data_by_batch_id(data['selected_experiment'])
    start_idx, end_idx = slider_range
    if not dfc.empty:
        timestamps = sorted(dfc["_time"].dropna().unique())
        start_time = timestamps[start_idx] if start_idx < len(timestamps) else timestamps[0]
        end_time = timestamps[end_idx] if end_idx < len(timestamps) else timestamps[-1]

        start_str = pd.to_datetime(start_time).strftime('%Y-%m-%d %H:%M:%S')
        end_str = pd.to_datetime(end_time).strftime('%Y-%m-%d %H:%M:%S')

        return f"From: {start_str}  ➡  To: {end_str}", len(timestamps)
    return "", 0

@dash.callback(
    Output("selected-variables-maintenance", "data", allow_duplicate=True),
    Output("variable-table-maintenance", "children"),
    Input("add-variable-btn-maintenance", "n_clicks"),
    Input({"type": "remove-btn", "index": ALL}, "n_clicks"),
    [State('name-selector-maintenance', 'value'),
     State("selected-variables-maintenance", "data")],
    prevent_initial_call=True
)
def update_table(add_click, remove_clicks, selected_variable, current_data):
    """
    Updates the table of monitored variables during maintenance.

    This callback handles both adding and removing variables from the
    variable list, dynamically generating the table to display them.

    Args:
        add_click (int): Number of clicks on the "Add" button.
        remove_clicks (list): List of click counts for each "Remove" button.
        selected_variable (str): The variable selected from the dropdown to add.
        current_data (list): Current list of variables being monitored.

    Returns:
        tuple: A tuple containing:
            - list: Updated list of selected variables.
            - dbc.Table: Updated table displaying the variables and actions.
    """
    if current_data is None:
        current_data = []

    # Check if Add button is clicked
    if ctx.triggered_id == "add-variable-btn-maintenance" and add_click:
        # Validate that the variable is not already in the list
        if selected_variable and selected_variable not in [v["variable_name"] for v in current_data]:
            current_data.append({"variable_name": selected_variable})

    # Check if Remove button is clicked
    elif isinstance(ctx.triggered_id, dict) and ctx.triggered_id["type"] == "remove-btn":
        index_to_remove = ctx.triggered_id["index"]
        if 0 <= index_to_remove < len(current_data):
            current_data.pop(index_to_remove)

    # Generate the table rows dynamically
    rows = [
        html.Tr([
            html.Td(variable["variable_name"], className="text-center"),
            html.Td(
                dbc.Button(
                    "Remove",
                    id={"type": "remove-btn", "index": int(i)},
                    color="danger",
                    size="sm",
                    className="remove-btn text-center"
                )
            )
        ]) for i, variable in enumerate(current_data)
    ]

    # Add table header
    table_header = html.Tr([
        html.Th("Variable monitoring", className="text-center"),
        html.Th("Action", className="text-center")
    ])
    table_body = [table_header] + rows

    # Wrap table with compact class
    table = dbc.Table(table_body, bordered=True, hover=True, striped=True, className="table-sm text-center")
    
    return current_data, table

@dash.callback(
    Output("save-confirmation", "children"),
    Input("confirm-save-btn", "n_clicks"),
    State("store-selected-state", "data"),
    State("model-data-store", "data"),
    State("prediction-table", "data"),
    State("clicked-report-info", "data"),
    State("dropdown-nivel", "value"),
    State("dropdown-tipo", "value"),
    State("description-flagged", "value"),
    prevent_initial_call=True
)
def save_selected_row_to_influx(n_clicks, data_exp, data, table_data, row_data, nivel, tipo, desc_flag):
    """
    Saves the selected row to SQLite with associated anomaly tags and an optional description.

    This callback is triggered when the user confirms a save action for a reported anomaly.
    It validates the required inputs, extracts the prediction value, and stores it 
    along with metadata in the local SQLite database (InfluxDB integration optional).

    Args:
        n_clicks (int): Number of times the "Confirm Save" button has been clicked.
        data_exp (dict): Dictionary containing the selected experiment information.
        data (dict): Dictionary with model metadata, including model_id.
        table_data (list): List of table data records displayed in the UI.
        row_data (dict): Data of the row selected via the "Report" link.
        nivel (str): Selected severity level for the anomaly.
        tipo (str): Selected anomaly type.
        desc_flag (str): Optional description entered for the anomaly.

    Returns:
        str: Confirmation or error message to display to the user.
    """
    if not row_data or "raw_time" not in row_data:
        return "⚠ Please select a valid row by clicking Report."

    if not nivel or not tipo:
        return "⚠ Please select both Level and Flag type."

    try:
        prediction_var = data["model_id"].lower()
        value = row_data.get("raw_prediction")

        if value is None or value == "":
            return "⚠ The prediction value is empty."

        tags = {
            "level": str(nivel),
            "type": str(tipo)
        }

        # Add optional description tag if provided
        if desc_flag:
            tags["description"] = desc_flag

        # Save in local SQLite (InfluxDB optional)
        sqlite_handler.upsert_point(
            data_exp["selected_experiment"],
            row_data["raw_time"],
            prediction_var,
            float(value),
            tags
        )

        return "✅ Point saved with tags in SQLite."

    except Exception as e:
        return f"❌ Error saving the point: {e}"
    
@dash.callback(
    Output("anomaly-warning", "style"),
    Input("prediction-table", "data")
)
def toggle_anomaly_warning(table_data):
    """
    Toggles the visibility of the anomaly warning message based on table data availability.

    This callback controls whether the anomaly warning is displayed.
    If the prediction table contains data, the warning is shown; otherwise, it is hidden.

    Args:
        table_data (list): Data displayed in the prediction table.

    Returns:
        dict: A dictionary with the CSS display style ("block" or "none").
    """
    if table_data and len(table_data) > 0:
        return {"display": "block"}
    return {"display": "none"}

@dash.callback(
    Output("save-modal", "is_open", allow_duplicate=True),
    Input("confirm-save-btn", "n_clicks"),
    Input("cancel-save-btn", "n_clicks"),
    State("clicked-report-info", "data"),
    prevent_initial_call=True
)
def process_report(confirm_clicks, cancel_clicks, report_data):
    """
    Handles the behavior of the save modal for anomaly reporting.

    This callback determines whether to close the modal when the user confirms or cancels
    the save action. If the confirmation button is clicked, the anomaly information is printed
    (and can later be stored in a database). If the cancel button is clicked, the modal closes
    without any action.

    Args:
        confirm_clicks (int): Number of clicks on the confirm save button.
        cancel_clicks (int): Number of clicks on the cancel button.
        report_data (dict): Data associated with the clicked report (e.g., anomaly details).

    Returns:
        bool | dash.no_update: Returns False to close the modal or dash.no_update to leave it unchanged.
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "cancel-save-btn":
        return False  # Close the modal without performing any action

    if trigger_id == "confirm-save-btn":
        # Log or save the anomaly report (future implementation)
        print(f"✅ Anomaly reported at: {report_data}")
        # TODO: Implement save or data transmission logic
        return False  # Close the modal after confirmation

    return dash.no_update

@dash.callback(
    Output("save-modal", "is_open"),
    Output("clicked-report-info", "data"),
    Input("prediction-table", "active_cell"),
    State("prediction-table", "data"),
    prevent_initial_call=True
)
def handle_report_click(active_cell, table_data):
    """
    Opens the save modal and stores the selected row data when the "Report" cell is clicked.

    This callback checks if the user clicked the "Report" column in the prediction table.
    If so, it retrieves the corresponding row data and opens the modal window to allow
    further actions, such as saving or tagging the anomaly.

    Args:
        active_cell (dict): Information about the currently clicked cell in the table.
        table_data (list[dict]): List of dictionaries representing the table data.

    Returns:
        tuple:
            - bool: True to open the modal, False otherwise.
            - dict | dash.no_update: The row data if a valid cell was clicked, otherwise no update.
    """
    if active_cell and active_cell.get("column_id") == "Report":
        row_idx = active_cell["row"]
        row_data = table_data[row_idx]
        print("row_data", row_data)
        return True, row_data  # Open modal with the selected row data

    return False, dash.no_update

@dash.callback(
    Output("download-excel-report", "data"),
    Input("generate-report-btn", "n_clicks"),
    Input("model-data-store", "data"),
    State("experiment-id-display-maintenence", "children"),
    State("model-selector-maintenance", "value"),
    State("time-window-slider", "value"),
    State("selected-variables-maintenance", "data"),
    State("prediction-table", "data"),
    prevent_initial_call=True
)
def generate_excel_report(n_clicks, data, experiment_id, model_selected, time_range, selected_vars, table_data):
    """
    Generate an Excel report containing metadata, simulation results, and flagged measurements.

    This callback creates an Excel file with three sheets:
        1. "Metadata" — General information about the experiment and model.
        2. "Simulation" — The prediction table with the selected variables and their simulation results.
        3. "Flagged Measurements_DB" — Data retrieved from the SQLite database containing flagged points.

    Args:
        n_clicks (int): Number of clicks on the "Generate Report" button.
        data (dict): Information about the model currently in use.
        experiment_id (str): The experiment identifier displayed in the interface.
        model_selected (str): The name of the selected model.
        time_range (list[int]): The start and end indices of the selected time window.
        selected_vars (list[dict]): List of variables selected for monitoring.
        table_data (list[dict]): The prediction data displayed in the table.

    Returns:
        dash.Output: A downloadable Excel file containing the report.
    """
    # Get prediction variable name
    prediction_var = data["model_id"].lower()

    # Sheet 1: General Metadata
    info_dict = {
        "Experiment ID": [experiment_id],
        "User": ["Admin"],
        "Selected model": [model_selected],
        "Time range start": [time_range[0]],
        "Time range end": [time_range[1]],
        "Selected variables": [", ".join([f"{v['variable_name']}" for v in selected_vars])],
        "Model metadata": [f"{BASE_URL_API}/metadata/{prediction_var.split('_')[-1]}"],
        "Database": [DB_ENGINE],
        "Bucket": [INFLUXDB_BUCKET_RAW],
    }
    df_info = pd.DataFrame(info_dict)

    # Sheet 2: Prediction Data
    df_prediction = pd.DataFrame(table_data)
    selected_columns = [v['variable_name'] for v in selected_vars]

    columns_dict = {
        "Timestamp": df_prediction["raw_time"],
        "Simulation": df_prediction["raw_prediction"]
    }

    # Add only the selected variables if they exist in the DataFrame
    for var in selected_columns:
        if var in df_prediction.columns:
            columns_dict[var] = df_prediction[var]

    df_transformed_pred = pd.DataFrame(columns_dict)

    # Sheet 3: Flagged Data from SQLite (point_report)
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_path, "..", "Data", "point_report.db")
        conn = sqlite3.connect(db_path)
        df_report = pd.read_sql_query(
            "SELECT * FROM point_report WHERE measurement = ?",
            conn,
            params=(experiment_id,)
        )
        conn.close()

        df_transformed_report = pd.DataFrame({
            "timestamp": df_report["time"],
            "_measurement": "Experiment ID",  # Fixed value
            "measurement_value": df_report["measurement"],
            "tag_1": df_report["type"],
            "tag_2": df_report["level"],
            "field_1": df_report["prediction_var"],
            "field_value": df_report["value"]
        })
    except Exception as e:
        df_report = pd.DataFrame({"error": [str(e)]})
        df_transformed_report = pd.DataFrame({"error": [str(e)]})

    # Merge simulation data with tags (type, level, description)
    if not df_transformed_pred.empty and not df_report.empty:
        df_transformed_pred["Timestamp"] = pd.to_datetime(df_transformed_pred["Timestamp"], format="ISO8601")
        df_report["time"] = pd.to_datetime(df_report["time"], format="ISO8601")

        df_transformed_pred = pd.merge(
            df_transformed_pred,
            df_report[["time", "type", "level", "description"]],
            left_on="Timestamp",
            right_on="time",
            how="left"
        )

        df_transformed_pred.drop(columns=["time"], inplace=True)
        df_transformed_pred["Timestamp"] = df_transformed_pred["Timestamp"].astype(str)

    # Create the Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_info.to_excel(writer, index=False, sheet_name="Metadata")
        df_transformed_pred.to_excel(writer, index=False, sheet_name="Simulation")
        df_transformed_report.to_excel(writer, index=False, sheet_name="Flagged Measurements_DB")
    output.seek(0)

    return dcc.send_bytes(output.read(), filename="report.xlsx")

