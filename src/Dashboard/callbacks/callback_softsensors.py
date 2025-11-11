import dash
from dash import Input, Output, State, html, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from Dashboard.utils import model_information
from Dashboard.InfluxDb import influxdb_handler # retrieve the created instance
from Dashboard.utils.utils_sofsensors_offline import reload_models
from Dashboard.utils.utils_softsensors import (create_toast,build_figure_with_traces,update_xaxis_range,
                                                    get_latest_index,build_figure_from_data,init_data_prediction,append_prediction,update_axes_labels)
from Dashboard.pages.model_details_view import generate_model_details_view
import pandas as pd
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

is_query_running = False

@dash.callback(
            Output("experiment-id-display-on", "children"),
            Input("store-selected-state", "data")
        )
def update_experiment_display(data):
            if not data or "selected_experiment" not in data:
                return "No Experiment Selected"
            return f"Selected Experiment ID: {data['selected_experiment']}"
      
@dash.callback(
    Output("selected-variables", "data", allow_duplicate=True),
    Output("variable-table", "children"),
    Input("add-variable-btn", "n_clicks"),
    Input({"type": "remove-btn", "index": ALL}, "n_clicks"),
    [
        State("name-selector", "value"),
        State("selected-variables", "data")
    ],
    prevent_initial_call=True
)
def update_table(add_click, remove_clicks, selected_variable, current_data):
    """
    Updates the variable table and the list of selected variables in the Dash app.

    This callback handles two actions:
    1. Adding a new variable to the list when the "Add Variable" button is clicked.
    2. Removing a variable when its corresponding "Remove" button is clicked.

    Args:
        add_click (int): Number of clicks on the "Add Variable" button.
        remove_clicks (list[int]): Number of clicks for each "Remove" button.
        selected_variable (str): Name of the variable currently selected by the user.
        current_data (list[dict]): Current list of selected variables.

    Returns:
        tuple: Updated `current_data` (list of dicts) and the updated HTML table (`dbc.Table`).
    """
    if current_data is None:
        current_data = []

    trigger = ctx.triggered_id

    # Add variable
    if trigger == "add-variable-btn" and add_click:
        # Add variable only if it is not already present
        if selected_variable and selected_variable not in [v["variable_name"] for v in current_data]:
            current_data.append({"variable_name": selected_variable})

    # Remove variable by name (trigger is a dict with index = variable_name)
    elif isinstance(trigger, dict) and trigger.get("type") == "remove-btn":
        name_to_remove = trigger.get("index")
        # Filter out the element with that name
        current_data = [v for v in current_data if v["variable_name"] != name_to_remove]

    # Generate table rows (using variable name as index in the id)
    rows = []
    for variable in current_data:
        name = variable["variable_name"]
        rows.append(
            html.Tr([
                html.Td(name, className="text-center"),
                html.Td(
                    dbc.Button(
                        "Remove",
                        id={"type": "remove-btn", "index": name},
                        color="danger",
                        size="sm",
                        className="remove-btn text-center"
                    )
                )
            ])
        )

    # Table header
    table_header = html.Tr([
        html.Th("Variable monitoring", className="text-center"),
        html.Th("Action", className="text-center")
    ])

    # Create table with Bootstrap styles
    table = dbc.Table([table_header] + rows, bordered=True, hover=True, striped=True, className="table-sm text-center")

    return current_data, table


@dash.callback(
            Output('name-selector', 'options'),
            Input('type-selector', 'value'),
            Input('model-selector', 'value')
        )
def update_name_selector(selected_category,model_name):
            """
            Update the options for the 'name-selector' dropdown based on the selected category.

            Args:
                selected_category (str): The category selected in the 'type-selector' dropdown.

            Returns:
                list: A list of dictionaries with the options for the 'name-selector' dropdown.
            """
            if selected_category:
                # Get names corresponding to the selected category
                return model_information.get_names_by_category(selected_category,model_name)
            else:
                # Return an empty list if no category is selected
                return []

# Function to update the options of the existing models
@dash.callback(
    Output('model-selector', 'options'),
    Output('model-selector', 'value'),
    Input('model-data-store', 'data')
)
def update_model_options(data_store):
    reload_models()
    options = model_information.get_model_name_options()

    selected_value = None
    if data_store and "selected_model" in data_store:
        selected_value = data_store["selected_model"]

    return options, selected_value

        
        # Function to update the ypes  of model inputs
@dash.callback(
            Output('type-selector', 'options'),
            Input('model-selector', 'value'),
            prevent_initial_call=True
        )
def update_model_types(name):
            #print("name",name)
            types_variable = model_information.get_unique_types_models(name)
            #print("types_variable",types_variable)
            return types_variable 

@dash.callback(
    [Output('model-details', 'children'),
     Output('model-data-store', 'data', allow_duplicate=True)],
    Input('model-selector', 'value'),
    prevent_initial_call=True
)
def display_model_details(selected_model):
    if not selected_model:
        return html.P("Select a model to show configuration.", style={'textAlign': 'center'}), {}

    config = model_information.get_configuration_by_model_name_language(selected_model)

    if config:
        model_data = {
            "selected_model": selected_model, 
            "model_id": config['model_identification'].get('ID', 'N/A'),
            "model_file": config['model_description'].get('config_files', {}).get('model_file', 'N/A'),
            "model_name": config['model_description'].get('model_name', 'N/A'),
            "language": config['model_description'].get('language', 'N/A'),
            "predictions": config['outputs'],
            "features": config['inputs']
        }
        return generate_model_details_view(config), model_data
    else:
        return html.P("The configuration for the selected model was not found.", style={'textAlign': 'center'}), {}

@dash.callback(
    Output(component_id='line-chart-prediction-on', component_property='figure', allow_duplicate=False),
    Output("prediction-data", "data"),
    Output("store-inicio-pred", "data"),
    Output("toast-message", "children"),
    Input('model-data-store', 'data'),
    Input("store-selected-state", "data"),
    Input(component_id='interval-component', component_property='n_intervals'),
    Input('line-chart-prediction-on', 'relayoutData'),
    State('prediction-data', 'data'),
    State("selected-variables", 'data'),
    State("store-inicio-pred", "data"),
    Input(component_id='run-on', component_property='n_clicks'),
    prevent_initial_call='initial_duplicate',
)
def update_graph(data_model, store_data, n, relayout_data, data_prediction, selected_variables, inicio_pred, n_clicks):
    """
    Updates the prediction graph with real-time data and model predictions.

    This function handles:
    - Loading new data from InfluxDB.
    - Updating the figure when new points arrive.
    - Managing multi-axis labels for selected variables.
    - Keeping previous x-axis zoom levels.
    - Generating toast notifications in case of missing data.

    Args:
        data_model (dict): Information about the selected model.
        store_data (dict): Information about the current experiment selection.
        n (int): Number of intervals triggered.
        relayout_data (dict): Current layout/zoom state of the plot.
        data_prediction (dict): Current stored prediction data.
        selected_variables (list): Variables selected to display on the graph.
        inicio_pred (int): Index of the last prediction data processed.
        n_clicks (int): Number of times the run button was clicked.

    Returns:
        tuple: (updated_figure, updated_prediction_data, updated_start_index, toast_message)
    """
    global is_query_running
    # Prevent running if already in progress
    if is_query_running:
        logger.debug("⚠️ Skipping update: previous query still running.")
        raise dash.exceptions.PreventUpdate 
    try:
        is_query_running = True  # lock on
        # ⛔ Wait until the button is pressed at least once
        if n_clicks == 0 or store_data is None or "selected_experiment" not in store_data:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        if "model_file" not in data_model or data_model["model_file"] is None:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update

        #inicio_pred = get_latest_index(store_data['selected_experiment'])
        logger.debug(f"n_clicks : {n_clicks}")
        dfc = influxdb_handler.get_data_until_latest(store_data['selected_experiment'])
        if dfc is None or dfc.empty:
            inicio_pred =  0
        
        inicio_pred = len(dfc) - 1

        fig = go.Figure()
        # Initialize empty dictionaries for axes
        y_axes = {}
        y_axis_labels = {}

        #dfc = influxdb_handler.get_data_until_latest(store_data['selected_experiment'])
        logger.debug(f"dfc columns: {dfc.columns}")
        # Using hardcoded model name (should match columns in dfc)
        #logger.debug(f"indo model:\n {data_model}")
        name_prediction = data_model["model_id"].lower()
        #name_prediction = "lstm"

        logger.debug(f"name_prediction: {name_prediction} selected_variables: {selected_variables}")

    
        data_prediction = init_data_prediction(dfc, selected_variables, name_prediction)
        
        logger.debug(f"inicio_pred : {inicio_pred} \n (len(dfc) : {len(dfc)}")

        if name_prediction not in dfc.columns:
            logger.info(
                f"⚠️ Column '{name_prediction}' not found in DataFrame. Available columns: {list(dfc.columns)}"
            )
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                create_toast(
                    f"Warning: No prediction for experiment id {store_data['selected_experiment']} with model name {name_prediction}",
                    5000
                )
            )

        if inicio_pred == (len(dfc) - 1):
            logger.debug(f"⏳ No new data yet (index_pred={inicio_pred}, total={len(dfc)}).")
            #logger.debug(f"data_prediction elements: \n {data_prediction}")
            y_axes, y_axis_labels = update_axes_labels(data_prediction, selected_variables, name_prediction)
            #logger.debug(f"y_axes: {y_axes} \n, y_axis_labels: {y_axis_labels} ")
            fig = build_figure_with_traces(data_prediction, selected_variables, name_prediction, y_axes, y_axis_labels)
            
            # Keep previous x-axis zoom if available
            fig = update_xaxis_range(fig, relayout_data, data_prediction)
            #logger.debug(f"fig: {fig}")
            return fig, data_prediction, inicio_pred, dash.no_update

        if inicio_pred < (len(dfc) - 1):
            # Generate penicillin predictions
            predicted_values = dfc
            if predicted_values is None:
                logger.warning(f"⚠️ No data beyond index inicio_pred: {inicio_pred}.")
                return dash.no_update, data_prediction, inicio_pred, dash.no_update

            logger.debug(f"name_prediction: {name_prediction}")  # Verify predictions
            if predicted_values is None or pd.isna(predicted_values.get(name_prediction)):
                logger.info(
                    f"[inicio_pred = {inicio_pred}] predicted_values[name_prediction] = NA or None: {predicted_values}"
                )
                # 🔁 Reuse previous data and continue showing the graph
                fig = build_figure_from_data(data_prediction, selected_variables, name_prediction)
                # Keep previous x-axis zoom if available
                fig = update_xaxis_range(fig, relayout_data, data_prediction)
                return fig, data_prediction, inicio_pred, dash.no_update

            if predicted_values is not None and not predicted_values.empty:
                data_prediction = append_prediction(data_prediction, predicted_values, name_prediction, selected_variables)
                y_axes, y_axis_labels = update_axes_labels(data_prediction, selected_variables, name_prediction)
                fig = build_figure_with_traces(data_prediction, selected_variables, name_prediction, y_axes, y_axis_labels)

        # Keep previous x-axis zoom if available
        fig = update_xaxis_range(fig, relayout_data, data_prediction)

        return fig, data_prediction, inicio_pred, dash.no_update
    except Exception as e:
        logger.error(f"Error updating graph: {e}")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    finally:
        is_query_running = False  # unlock always, even on error

@dash.callback(
    Output('slider-value-output', 'children'),
    Output('interval-component', 'interval'),
    Input('interval-seconds-input', 'value')
)
def update_interval_display(seconds):
    return f"Interval update (seconds): {seconds}", seconds * 1000

@dash.callback(
    Output("prediction-data", "data", allow_duplicate=True),
    Output("previous-model", "data"),
    Input("model-selector", "value"),
    State("previous-model", "data"),
    State("prediction-data", "data"),
    prevent_initial_call=True
)
def reset_prediction_store(selected_model, previous_model, current_prediction_data):
    # Si previous_model es None → mantener datos
    if previous_model is None:
        return current_prediction_data or {}, selected_model

    # Reset solo si el modelo cambió
    if selected_model != previous_model:
        logger.info("Model changed → reset")
        return {}, selected_model

    # Si no cambió → mantener datos
    return current_prediction_data or {}, previous_model

@dash.callback(
    Output("interval-component", "disabled"),
    Input("run-on", "n_clicks"),
)
def activate_interval(n_clicks):
    if n_clicks and n_clicks > 0:
        return False
    return True    





