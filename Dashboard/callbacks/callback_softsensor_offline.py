import dash
from dash import Input, Output, State, html,ALL,ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from utils import model_information
from InfluxDb import influxdb_handler # retrieve the created instance
from utils.utils_sofsensors_offline import reload_models, generate_predictions, generate_prediction_name # the necessary utils functions for the callbacks are loaded
from pages.model_details_view import generate_model_details_view
import pandas as pd
import plotly.express as px


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
            Output("line-chart-prediction-off", "figure", allow_duplicate=True),  
            Input({"type": "remove-btn", "index": ALL}, "n_clicks"),
            State("selected-variables-off", "data"),
            State("line-chart-prediction-off", "figure"),
            prevent_initial_call=True
        )
def remove_graph_var(n_clicks, selected_variables, current_figure):
            """
            Removes only the trace of the corresponding variable when its delete button is pressed.
            """
            if not any(n_clicks):  # If no button has been pressed, do nothing
                raise PreventUpdate  

            if not current_figure or "data" not in current_figure:
                raise PreventUpdate  # Prevent errors if the figure is empty

            fig = go.Figure(current_figure)  # Keep the original figure

            # Identify which buttons were pressed
            clicked_indices = [i for i, click in enumerate(n_clicks) if click]

            if not clicked_indices or not selected_variables:
                raise PreventUpdate  

            # Variables to remove
            variables_to_remove = set(
                selected_variables[i]["variable_name"]
                for i in clicked_indices
                if i < len(selected_variables) and "variable_name" in selected_variables[i]
            )

            print(f"❌ Removing variables from the graph: {variables_to_remove}")

            # Filter traces and remove only the necessary ones
            #fig.data = tuple(trace for trace in fig.data if trace.name not in variables_to_remove)
            new_traces = [trace for trace in fig.data if trace.name not in variables_to_remove]
            # Crear una nueva figura con los datos filtrados
            new_fig = go.Figure(data=new_traces, layout=fig.layout)

            print(f"📉 Updated graph. Remaining variables: {[trace.name for trace in new_fig.data]}")
            return new_fig

            
@dash.callback(
            Output("selected-variables-off", "data", allow_duplicate=True),
            Output("variable-table-off", "children"),
            Input("add-variable-btn", "n_clicks"),
            Input({"type": "remove-btn", "index": ALL}, "n_clicks"),
            [State('name-selector-off', 'value'),
            State("selected-variables-off", "data")],
            prevent_initial_call=True
        )
def update_table(add_click, remove_clicks, selected_variable, current_data):
            if current_data is None:
                current_data = []

            # Check if Add button is clicked
            if ctx.triggered_id == "add-variable-btn" and add_click:
                #Validate that the variable is not already in the list
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
            table_header = html.Tr([html.Th("Variable monitoring", className="text-center"), html.Th("Action", className="text-center")])
            table_body = [table_header] + rows

            # Wrap table with compact class
            table = dbc.Table(table_body, bordered=True, hover=True, striped=True, className="table-sm text-center")
            return current_data, table


@dash.callback(
            Output('name-selector-off', 'options'),
            Input('type-selector-on', 'value'),
            Input('model-selector-off', 'value')
        )
def update_name_selector(selected_category,model_name):
            """
            Update the options for the 'name-selector-off' dropdown based on the selected category.

            Args:
                selected_category (str): The category selected in the 'type-selector-on' dropdown.

            Returns:
                list: A list of dictionaries with the options for the 'name-selector-off' dropdown.
            """
            if selected_category:
                # Get names corresponding to the selected category
                return model_information.get_names_by_category(selected_category,model_name)
            else:
                # Return an empty list if no category is selected
                return []
        # Function to update the options of the existing models
@dash.callback(
            Output('model-selector-off', 'options'),
            Input('model-selector-off', 'n_clicks')
        )
def update_model_options(n_clicks):
    reload_models()
    return model_information.get_model_name_options()
        
        # Function to update the ypes  of model inputs
@dash.callback(
            Output('type-selector-on', 'options'),
            Input('model-selector-off', 'value'),
            prevent_initial_call=True
        )
def update_model_types(name):
    types_variable = model_information.get_unique_types_models(name)
    return types_variable 

@dash.callback(
            [Output('model-details-off', 'children'),
            Output('model-data-store', 'data', allow_duplicate=True)],  # Updates the Store
            Input('model-selector-off', 'value'), 
            prevent_initial_call=True
        )
def display_model_details(selected_model):
            if not selected_model:
                return html.P("Select a model to show configuration.", style={'textAlign': 'center'}), {}

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
            Output("line-chart-prediction-off", "figure"),  # Graph where new variables will be added
            Input("add-variable-btn", "n_clicks"),  # Button to add variables
            Input("selected-variables-off", "data"),  # Variables selected by the user
            State("line-chart-prediction-off", "figure"),  # Current state of the graph
            prevent_initial_call=True  # Prevents automatic execution
        )
def update_graph_var(n_clicks, selected_variables, current_figure):
            global dfc

            print(f"🔄 Callback executed - Clicks: {n_clicks}, Selected variables: {selected_variables}")

            if not selected_variables:
                print("⚠ No variables selected. The graph will not be updated.")
                return go.Figure(current_figure) if current_figure else go.Figure()

            if dfc is None or "_time" not in dfc:
                print("⚠ No data in dfc or missing '_time' column.")
                return go.Figure(current_figure) if current_figure else go.Figure()

            df = pd.DataFrame(dfc)
            df["_time"] = pd.to_datetime(df["_time"], errors="coerce")

            fig = go.Figure(current_figure) if current_figure else go.Figure()

            existing_traces = {trace.name for trace in fig.data}
            print(f"📊 Already plotted variables: {existing_traces}")

            colors = px.colors.qualitative.Dark24  

            # Identify existing Y axes in the layout
            existing_y_axes = {k for k in fig.layout if k.startswith("yaxis")}
            num_existing_y_axes = len(existing_y_axes)

            # Iterate over each selected variable and add it if not already plotted
            for i, var_data in enumerate(selected_variables):
                if not isinstance(var_data, dict) or "variable_name" not in var_data:
                    print(f"⚠ Unexpected format in selected_variables[{i}]: {var_data}")
                    continue

                var = var_data["variable_name"]

                if var in df.columns and var not in existing_traces:
                    color = colors[num_existing_y_axes % len(colors)]  
                    y_axis_name = f"yaxis{num_existing_y_axes + 1}"  # yaxis2, yaxis3, etc.
                    y_axis_ref = f"y{num_existing_y_axes + 1}"  # y2, y3, etc.

                    # Add trace with its own Y axis
                    fig.add_trace(go.Scatter(
                        x=df["_time"].astype(str),
                        y=df[var],
                        mode="lines",
                        name=var,
                        yaxis=y_axis_ref,  
                        line=dict(color=color)
                        
                    ))

                    # Add new Y axis to the layout
                    fig.update_layout(**{
                        y_axis_name: dict(
                            title=dict(text=var, font=dict(color=color)),  
                            tickfont=dict(color=color),
                            anchor="x",
                            overlaying="y",  
                            side= 'right',
                            position =  1 - (0.10 * (num_existing_y_axes+1 - 2)),
                            showgrid=False
                        )
                    })

                    num_existing_y_axes += 1

                    print(f"✅ Variable '{var}' added with axis {y_axis_ref}.")

                else:
                    print(f"⚠ Variable '{var}' is already plotted or does not exist in the data.")

            # Configure general graph layout
            fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickangle=-45,
                    type="date"
                ),
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                )
            )

            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=[
                            dict(count=6, label="6 hours", step="hour", stepmode="backward"),
                            dict(count=1, label="1 day", step="hour", stepmode="backward"),
                            dict(count=1, label="1 month", step="month", stepmode="backward"),
                            dict(step="all")
                        ]
                    ),
                  
                    type="date"
                )
            )       

            print(f"📊 Graph updated with {len(fig.data)} variables and multiple Y axes.")

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
                return ({'data': [], 'layout': {}}, None)  
            # Get the data for the selected batch
            dfc = influxdb_handler.get_data_by_batch_id2(store_data['selected_experiment'])
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
                            side="left"
                        ),
                        legend=dict(
                            orientation="h",
                            yanchor="top",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        )
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
