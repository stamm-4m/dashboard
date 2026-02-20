import dash
from dash import Input, Output, State, html,ALL,ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from Dashboard.InfluxDb import influxdb_handler # retrieve the created instance
from Dashboard.utils.utils_global import disabled_figure
from Dashboard.utils.utils_model_information import get_model_information
from Dashboard.utils.utils_sofsensors_offline import reload_models, generate_predictions, generate_prediction_name # the necessary utils functions for the callbacks are loaded
from Dashboard.pages.model_details_view import generate_model_details_view
import pandas as pd
import plotly.express as px
from datetime import datetime

# Control start prediction
inicio_pred = 0
dfc = pd.DataFrame()




@dash.callback(
            Output("experiment-id-display-off", "children"),
            Input("store-selected-state", "data")
        )
def update_experiment_display(data):
            if not data or "selected_experiment" not in data:
                return "No Experiment Selected"
            return f"Selected Experiment ID: {data['selected_experiment']}"


@dash.callback(
    Output("selected-variables-off", "data", allow_duplicate=True),
    Output("variable-table-off", "children"),
    Input("add-variable-btn", "n_clicks"),
    Input({"type": "remove-btn", "var": ALL}, "n_clicks"),  # ✅ usamos 'var'
    [State('name-selector-off', 'value'),
     State("selected-variables-off", "data")],
    prevent_initial_call=True
)
def update_table(add_click, remove_clicks, selected_variable, current_data):
    """
    Update the list of selected variables and refresh the table when a variable is added or removed.

    Args:
        add_click (int): Click count for Add button.
        remove_clicks (list): Click counts for Remove buttons.
        selected_variable (str): Variable selected from dropdown.
        current_data (list): Current list of variables.

    Returns:
        tuple: (updated variable list, HTML table)
    """
    if current_data is None:
        current_data = []

    triggered_id = ctx.triggered_id  # Identify which input triggered the callback

    # ✅ Add new variable
    if triggered_id == "add-variable-btn" and add_click:
        if selected_variable and selected_variable not in [v["variable_name"] for v in current_data]:
            current_data = current_data + [{"variable_name": selected_variable}]  # force new list reference

    # ✅ Remove variable
    elif isinstance(triggered_id, dict) and triggered_id.get("type") == "remove-btn":
        var_to_remove = triggered_id.get("var")
        if var_to_remove:
            current_data = [v for v in current_data if v["variable_name"] != var_to_remove]

    # ✅ Build the updated table
    rows = [
        html.Tr([
            html.Td(variable["variable_name"], className="text-center"),
            html.Td(
                dbc.Button(
                    "Remove",
                    id={"type": "remove-btn", "var": variable["variable_name"]},  # ✅ 'var'
                    color="danger",
                    size="sm",
                    className="remove-btn text-center"
                )
            )
        ]) for variable in current_data
    ]

    table_header = html.Tr([
        html.Th("Variable Monitoring", className="text-center"),
        html.Th("Action", className="text-center")
    ])

    table = dbc.Table([table_header] + rows, bordered=True, hover=True, striped=True, className="table-sm text-center")

    print("✅ Updated current_data:", current_data)
    return current_data, table



@dash.callback(
            Output('name-selector-off', 'options'),
            Input('type-selector-on', 'value'),
            Input('model-selector-off', 'value'),
            State("store-selected-state", "data"),
        )
def update_name_selector(selected_category,model_name, store_data):
            """
            Update the options for the 'name-selector-off' dropdown based on the selected category.

            Args:
                selected_category (str): The category selected in the 'type-selector-on' dropdown.

            Returns:
                list: A list of dictionaries with the options for the 'name-selector-off' dropdown.
            """
            if selected_category:
                model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
                # Get names corresponding to the selected category
                return model_information.get_names_by_category(selected_category,model_name)
            else:
                # Return an empty list if no category is selected
                return []
        # Function to update the options of the existing models
@dash.callback(
            Output('model-selector-off', 'options'),
            Input('model-selector-off', 'n_clicks'),
            State("store-selected-state", "data")
        )
def update_model_options(n_clicks,store_data):
    reload_models(project_id=store_data.get("selected_project"))
    model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
    return model_information.get_model_name_options()
        
        # Function to update the ypes  of model inputs
@dash.callback(
            Output('type-selector-on', 'options'),
            Input('model-selector-off', 'value'),
            State("store-selected-state", "data"),
            prevent_initial_call=True
        )
def update_model_types(name, store_data):

    model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
    types_variable = model_information.get_unique_types_models(name)
    return types_variable 

@dash.callback(
            [Output('model-details-off', 'children'),
            Output('model-data-store', 'data', allow_duplicate=True)],  # Updates the Store
            Input('model-selector-off', 'value'), 
            State("store-selected-state", "data"),
            prevent_initial_call=True
        )
def display_model_details(selected_model, store_data):
            if not selected_model:
                return html.P("Select a model to show configuration.", style={'textAlign': 'center'}), {}

            model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
            config = model_information.get_configuration_by_model_name_language(selected_model)

            if config:
                model_data = {
                    "model_file": config['model_description'].get('config_files', {}).get('model_file', 'N/A'),
                    "model_name": config['model_description'].get('model_name', 'N/A'),
                    "language": config['model_description'].get('language', 'N/A'),
                    "predictions": config['outputs'].get('predictions', 'N/A'),
                    "features": config['inputs'].get('features', 'N/A')
                }
                return generate_model_details_view(config), model_data
            else:
                return html.P("The configuration for the selected model was not found.", style={'textAlign': 'center'}), {}

# Callback to initialize the prediction
@dash.callback(
    Output("line-chart-prediction-off", "figure"),
    Input("add-variable-btn", "n_clicks"),
    Input("selected-variables-off", "data"),
    State("line-chart-prediction-off", "figure"),
    prevent_initial_call=True
)
def sync_figure_with_store(n_clicks, selected_variables, current_figure):
    """
    Sync the graph with the selected-variables store:
     - Remove traces that are not in selected_variables (except prediction traces we keep).
     - Add traces for variables that are in selected_variables but missing in the figure.
    This keeps a single source of truth (the store) and avoids race conditions.
    """
    global dfc

    # Start from existing figure (or a new one)
    fig = go.Figure(current_figure) if current_figure else go.Figure()

    # Normalize helper
    def _norm(x):
        return str(x).strip().lower()

    # Build desired variables set from the store (source of truth)
    desired_vars = set()
    if selected_variables:
        desired_vars = {sv.get("variable_name") for sv in selected_variables if isinstance(sv, dict) and "variable_name" in sv}

    # Keep certain traces even if not in desired_vars (e.g. prediction traces)
    # Adjust this set if you have other "static" trace names you must preserve
    KEEP_TRACES = {"Penicillin Concentration"}

    # Current trace names (string normalized)
    current_traces = [(trace, str(trace.name)) for trace in fig.data]

    # 1) Remove traces that are not desired and not in KEEP_TRACES
    new_traces = [trace for trace, name in current_traces if (name in desired_vars) or (name in KEEP_TRACES)]

    # If something was removed, rebuild the figure to ensure a fresh object
    if len(new_traces) != len(fig.data):
        fig = go.Figure(data=new_traces, layout=fig.layout)

    # Recompute existing trace names after possible removal
    existing_trace_names = {str(t.name) for t in fig.data if t.name is not None}

    # 2) Add missing traces for desired_vars that are not yet plotted
    # Validate we have the dfc data
    if dfc is None or "_time" not in dfc:
        # No data available — just return the figure after removals
        print("⚠ No dfc or missing '_time' — only removals applied (if any).")
        # Force re-render
        fig.update_layout(uirevision=str(datetime.utcnow().timestamp()))
        fig.layout["meta"] = {"last_update": datetime.utcnow().isoformat()}
        return fig

    df = pd.DataFrame(dfc)
    df["_time"] = pd.to_datetime(df["_time"], errors="coerce")

    # Utility: determine current maximum y-axis index used in traces (1 = y)
    def _trace_axis_index(trace):
        # trace.yaxis can be 'y' or 'y2', etc. If missing, default to 1
        axis = getattr(trace, "yaxis", None)
        if not axis:
            return 1
        axis = str(axis)
        if axis == "y":
            return 1
        try:
            return int(axis.lstrip("y"))
        except:
            return 1

    existing_axis_indexes = [_trace_axis_index(t) for t in fig.data] if fig.data else [1]
    max_axis_index = max(existing_axis_indexes) if existing_axis_indexes else 1

    colors = px.colors.qualitative.Dark24

    for var in desired_vars:
        if var in existing_trace_names:
            # already plotted
            continue
        if var not in df.columns:
            print(f"⚠ Variable '{var}' not found in dfc columns; skipping.")
            continue

        # new axis index
        new_axis_index = max_axis_index + 1
        yaxis_name = f"yaxis{new_axis_index}"   # e.g. 'yaxis2'
        yaxis_ref = f"y{new_axis_index}"        # e.g. 'y2'

        color = colors[(new_axis_index - 1) % len(colors)]

        # add trace
        fig.add_trace(go.Scatter(
            x=df["_time"].astype(str),
            y=df[var],
            mode="lines",
            name=var,
            yaxis=yaxis_ref,
            line=dict(color=color)
        ))

        # add axis layout
        position = 1 - (0.10 * (new_axis_index - 2)) if new_axis_index >= 2 else 0  # keep similar logic you had
        fig.update_layout(**{
            yaxis_name: dict(
                title=dict(text=var, font=dict(color=color)),
                tickfont=dict(color=color),
                anchor="x",
                overlaying="y",
                side="right",
                position=position,
                showgrid=False
            )
        })

        max_axis_index = new_axis_index
        existing_trace_names.add(var)
        print(f"✅ Added trace for variable '{var}' on axis {yaxis_ref}.")

    # 3) Final layout polish and force re-render
    fig.update_layout(
        xaxis=dict(title="Time", tickangle=-45, type="date"),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    # range selector (preserve your previous config)
    fig.update_layout(xaxis=dict(rangeselector=dict(
        buttons=[
            dict(count=6, label="6 hours", step="hour", stepmode="backward"),
            dict(count=1, label="1 day", step="day", stepmode="backward"),
            dict(count=1, label="1 month", step="month", stepmode="backward"),
            dict(step="all")
        ]),
        type="date"
    ))

    fig.update_layout(uirevision=str(datetime.utcnow().timestamp()))
    fig.layout["meta"] = {"last_update": datetime.utcnow().isoformat()}

    print(f"📊 Sync finished. Traces now: {[t.name for t in fig.data]}")
    return fig
        
@dash.callback(
            Output('line-chart-prediction-off', 'figure',allow_duplicate=True),
            Output("prediction-data-off", "data"),
            Input('model-data-store', 'data'),
            Input("store-selected-state", "data"),
            Input(component_id='run', component_property='n_clicks'),
            State('prediction-data-off', 'data'),
            State("selected-variables-off", "data"),
            prevent_initial_call='initial_duplicate'
        )
def update_graph(data_model, store_data, n, data_prediction, selected_variables):
            global inicio_pred, dfc
            
            if store_data is None or 'selected_experiment' not in store_data:
                return (disabled_figure, None)  
            # Get the data for the selected batch
            dfc = influxdb_handler.get_data_by_batch_id(store_data['selected_experiment'])
            inicio_pred += 1  # Reset the prediction counter
            txt_prediction = generate_prediction_name("default_model.pkl")
           
            if "model_file" in data_model and data_model["model_file"]:
                txt_prediction = generate_prediction_name(data_model["model_file"])
            print("txt_prediction:",txt_prediction)
            

            print(f"🔄 Callback executed - Interval: {n}, Inicio_pred: {inicio_pred}")

            fig = go.Figure()

            if n > 0 and inicio_pred > 0:
                predicted_values = generate_predictions(store_data['selected_experiment'], data_model, inicio_pred)

                if predicted_values is None or predicted_values.empty:
                    print("⚠ No data in predicted_values.")
                    return fig, {"_time": [], txt_prediction: []}

                print(f"✅ {len(predicted_values)} records obtained for prediction.")

                # Convert `_time` to datetime and then to string
                predicted_values["_time"] = pd.to_datetime(predicted_values["_time"], errors="coerce").astype(str)
                
                if predicted_values["_time"].isnull().all():
                    print("⚠ Error: All `_time` values are null. Cannot plot.")
                    return fig, {"_time": [], txt_prediction: []}

                # Create structure to store data
                data_prediction = {
                    "_time": predicted_values["_time"].tolist(),
                    txt_prediction: []
                }

                # 🔹 Validate if `txt_prediction` exists in the data
                predicted_values.columns = predicted_values.columns.str.strip()  # Remove spaces in column names
                column_data = predicted_values.get(txt_prediction)

                if column_data is not None:
                    data_prediction[txt_prediction] = column_data.tolist()
                    print(f"📈 Found '{txt_prediction}' in the data. First 5 values:", data_prediction[txt_prediction][:5])

                    # Check that there are numeric values in `y`
                    if not any(pd.notna(data_prediction[txt_prediction])):
                        print("⚠ Error: All values of `penicillin_concentration` are null.")
                        return fig, data_prediction

                    # Convert `_time` back to datetime for proper plotting
                    data_prediction["_time"] = pd.to_datetime(data_prediction["_time"])

                    # Add trace to the graph
                    fig.add_trace(go.Scatter(
                        x=data_prediction["_time"].astype(str),
                        y=data_prediction[txt_prediction],
                        mode="lines",
                        name="Penicillin Concentration",
                        yaxis="y",
                        line=dict(color="blue")
                    ))

                    # Configure graph layout
                    fig.update_layout(
                        xaxis=dict(
                            title="Time",
                            tickangle=-45,
                            type="date"
                        ),
                        yaxis=dict(
                            title=txt_prediction,
                            title_font=dict(color="blue"),
                            tickfont=dict(color="blue"),
                            side="left",
                            hoverformat=".2f"
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="top",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        ),
                        hovermode="x unified"
                    )

                    fig.update_layout(
                        xaxis=dict(
                            rangeselector=dict(
                                buttons=[
                                    dict(count=6, label="6 hours", step="hour", stepmode="backward"),
                                    dict(count=1, label="1 day", step="day", stepmode="backward"),
                                    dict(count=1, label="1 month", step="month", stepmode="backward"),
                                    dict(step="all")
                                ]
                            ),
                           
                            type="date"
                        )
                    )

                else:
                    print(f"⚠ '{txt_prediction}' not found in the data.")

                inicio_pred += 1

            print(f"📊 Number of traces in the graph at the end: {len(fig.data)}")
            
            return fig, data_prediction
