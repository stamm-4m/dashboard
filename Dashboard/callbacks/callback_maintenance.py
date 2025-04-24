from dash import Input, Output, State, dcc, ALL, ctx, html
import dash_bootstrap_components as dbc
import dash
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from InfluxDb import influxdb_handler # retrieve the created instance
import io
from utils import model_selector
import plotly.express as px


dfc = pd.DataFrame()


""" @dash.callback(
        [
            Output("variable-store-maintenance", "data"),
            Output("variable-table-maintenance", "data"),
            Output("maintenance-graph", "figure"),
        ],
        Input("add-variable-btn-maintenance", "n_clicks"),
        State("model-selector-maintenance", "value"),
        State("type-selector-maintenance", "value"),
        State("name-selector-maintenance", "value"),
        State("variable-store-maintenance", "data"),
        prevent_initial_call=True
    )
def update_variable_table_and_graph(n_clicks, model, var_type, var_name, current_data):
        if not current_data:
            return current_data, current_data, go.Figure()

        new_entry = {"model": model, "type": var_type, "name": var_name}

        if model and var_type and var_name and new_entry not in current_data:
            current_data.append(new_entry)
        else:
            return current_data, current_data, dash.no_update

        # Simulated time-series data
        time = np.linspace(0, 225, 20)
        fig = go.Figure()

        for i, entry in enumerate(current_data):
            simulated_data = np.sin(time / 30 + i) + np.random.normal(scale=0.1, size=len(time))
            fig.add_trace(go.Scatter(
                x=time,
                y=simulated_data,
                mode='lines',
                name=f"{entry['model']} - {entry['name']}",
                line=dict(width=2)
            ))

        fig.update_layout(title="Model Variable Simulation", xaxis_title="Time", yaxis_title="Value")
        return current_data, current_data, fig
 """
# Save modal
@dash.callback(
        Output("save-modal", "is_open"),
        [Input("save-simulations", "n_clicks"), Input("cancel-save", "n_clicks")],
        [State("save-modal", "is_open")],
        prevent_initial_call=True
    )
def toggle_save_modal(save_click, cancel_click, is_open):
        return not is_open

# Download Excel
@dash.callback(
        Output("download-excel", "data"),
        Input("confirm-save", "n_clicks"),
        State("variable-table-maintenance", "data"),
        prevent_initial_call=True
    )
def save_simulation(n_clicks, data):
        if not data:
            return None

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Simulations")
        output.seek(0)

        return dcc.send_bytes(output.getvalue(), "simulation_data.xlsx")

# Maintain modal
@dash.callback(
        Output("maintain-modal", "is_open"),
        [Input("maintain-model", "n_clicks"), Input("cancel-maintain", "n_clicks")],
        [State("maintain-modal", "is_open")],
        prevent_initial_call=True
    )
def toggle_maintain_modal(maintain_click, cancel_click, is_open):
        return not is_open

# Confirm maintenance
@dash.callback(
        Output("maintain-reason", "value"),
        Input("confirm-maintain", "n_clicks"),
        State("maintain-reason", "value"),
        prevent_initial_call=True
    )
def confirm_maintenance(n_clicks, reason):
        if reason:
            print(f"Maintenance confirmed with reason: {reason}")
            return ""
        return dash.no_update

# Function to update the ypes  of model inputs
@dash.callback(
            Output('type-selector-maintenance', 'options'),
            Input('model-selector-maintenance', 'value'),
            prevent_initial_call=True
        )
def update_model_types_maintenance(name):
            #print("name",name)
            types_variable = model_selector.get_unique_types_models(name)
            #print("types_variable",types_variable)
            return types_variable
@dash.callback(
            Output('name-selector-maintenance', 'options'),
            Input('type-selector-maintenance', 'value'),
            Input('model-selector-maintenance', 'value')
        )
def update_name_selector(selected_category,model_name):
            """
            Update the options for the 'name-selector-maintenance' dropdown based on the selected category.

            Args:
                selected_category (str): The category selected in the 'type-selector-maintenance' dropdown.

            Returns:
                list: A list of dictionaries with the options for the 'name-selector-maintenance' dropdown.
            """
            if selected_category:
                # Get names corresponding to the selected category
                return model_selector.get_names_by_category(selected_category,model_name)
            else:
                # Return an empty list if no category is selected
                return []
            
# Callback to initialize the graph
@dash.callback(
            Output("maintenance-graph", "figure"),  # Graph where new variables will be added
            Input("add-variable-btn-maintenance", "n_clicks"),  # Button to add variables
            Input("selected-variables-maintenance", "data"),  # Variables selected by the user
            State("maintenance-graph", "figure"),  # Current state of the graph
            prevent_initial_call=True  # Prevents automatic execution
        )
def update_graph_var_maintenance(n_clicks, selected_variables, current_figure):
            global dfc
            dfc = influxdb_handler.get_data_by_batch_id2("32") #store_data['selected_experiment'])

            print("" )

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

            print(f"📊 Graph updated with {len(fig.data)} variables and multiple Y axes.")

            return fig
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
            if current_data is None:
                current_data = []

            # Check if Add button is clicked
            if ctx.triggered_id == "add-variable-btn-maintenance" and add_click:
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