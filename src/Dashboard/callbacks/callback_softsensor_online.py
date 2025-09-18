import dash
from dash import Input, Output, State, html, ALL, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from Dashboard.utils import model_information
from Dashboard.InfluxDb import influxdb_handler # retrieve the created instance
from Dashboard.utils.utils_sofsensors_offline import reload_models
from Dashboard.utils.utils_softsensors_online import create_toast, generate_predictions,generate_prediction_name
from Dashboard.pages.model_details_view import generate_model_details_view
import pandas as pd
import plotly.express as px
from Dashboard.utils.utils_global import disabled_figure

# Control start prediction
inicio_pred = 0



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
            [State('name-selector', 'value'),
            State("selected-variables", "data")],
            prevent_initial_call=True
        )
def update_table(add_click, remove_clicks, selected_variable, current_data):
            if current_data is None:
                current_data = []

            # Check if Add button is clicked
            if ctx.triggered_id == "add-variable-btn" and add_click:
                # Validar que la variable no esté ya en la lista
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
                            id={"type": "remove-btn", "index": int(i+1)},
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
            Input('model-selector', 'n_clicks')
        )
def update_model_options(n_clicks):
            reload_models()
            return model_information.get_model_name_options()
        
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
            Output('model-data-store', 'data', allow_duplicate=True)],  # Updates the Store
            Input('model-selector', 'value'), 
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
                    "predictions": config['outputs'],
                    "features": config['inputs']
                }
                return generate_model_details_view(config), model_data
            else:
                return html.P("The configuration for the selected model was not found.", style={'textAlign': 'center'}), {}
            

@dash.callback(
            Output(component_id='line-chart-prediction-on', component_property='figure',allow_duplicate=True),
            Output("prediction-data", "data"),
            Input('model-data-store', 'data'),
            Input("store-selected-state", "data"),
            Input(component_id='interval-component', component_property='n_intervals'),
            State('prediction-data','data'),
            State("selected-variables",'data'),
            Input(component_id='run-on', component_property='n_clicks'),
            prevent_initial_call='initial_duplicate'
        )
def update_graph(data_model, store_data, n,data_prediction, selected_variables,n_clicks):
            global  inicio_pred

            # ⛔ Espera a que el botón se presione al menos una vez
            if n_clicks == 0 or store_data is None or "selected_experiment" not in store_data:
                return dash.no_update, dash.no_update
            
            fig = go.Figure()
            # Initialize empty dictionaries
            y_axes = {}
            y_axis_labels = {}
            if "model_file" in data_model and data_model["model_file"]:
                # Generate penicillin predictions    
                name_prediction = generate_prediction_name(data_model["model_file"])
                predicted_values = generate_predictions(store_data['selected_experiment'], inicio_pred)
                print("predicted_values: ",predicted_values)
                if predicted_values is None:
                    print(f"⚠️ Not data out index inicio_pred:  {inicio_pred}.")
                    inicio_pred += 1
                    return dash.no_update, data_prediction
                
                print(f"name_prediction: {name_prediction}")  # Verify predictions
                if predicted_values is None or pd.isna(predicted_values.get(name_prediction)):
                    print(f"[{inicio_pred}] Valor NA: {predicted_values}")
                    inicio_pred += 1
                    return dash.no_update, data_prediction
                
                if predicted_values is not None and not predicted_values.empty:
                    
                    tiempo_pred = pd.to_datetime(predicted_values['_time']) # get first datetime
                    nivel_pred = predicted_values[name_prediction] # get first value

                    print(f"Updating prediction: {tiempo_pred}, {nivel_pred}")
                    # Add new data to storage
                    # ✔️ Inicializar si no hay datos anteriores
                    if data_prediction is None:
                        data_prediction = {}

                    # ✔️ Inicializar listas si no existen
                    if "_time" not in data_prediction:
                        data_prediction["_time"] = []
                    if name_prediction not in data_prediction:
                        data_prediction[name_prediction] = []

                    # ✔️ Agrega nuevo punto
                    data_prediction["_time"].append(tiempo_pred.strftime("%Y-%m-%d %H:%M:%S"))
                    data_prediction[name_prediction].append(nivel_pred)

                    # Get values of the variables
                    # Process variable data
                    i = 1
                    for variable in selected_variables:
                        var_name = variable["variable_name"]
                        axis = f"y{i}"  # Create axis name, like "y", "y2", etc.
                        # Assign variable and label name to dictionary
                        y_axes[var_name] = axis
                        y_axis_labels[axis] = var_name.capitalize()
                        i=i+1
                        if(variable["variable_name"] != name_prediction):
                            value_variable = predicted_values.get(variable["variable_name"])
                            if value_variable is None:
                                selected_variables = [var for var in selected_variables if var["variable_name"] in predicted_values]
                                create_toast(f"Warning: The variable '{variable['variable_name']}' is not part of the model.")
                            else:
                                # Continue processing if variable is present
                                if pd.isna(value_variable):
                                    print(f"Variable data {variable['variable_name']}: {value_variable}")
                                else:
                                    if variable["variable_name"] not in data_prediction:
                                        data_prediction[variable["variable_name"]] = []  # Create key with empty list
                                    
                                    data_prediction[variable["variable_name"]].append(value_variable)
                                    print(f"Variable data {variable['variable_name']}: {value_variable}")
                    # Dictionary to store colors for each variable
                    # Crear diccionario de colores incluyendo siempre la predicción
                    color_map = {var["variable_name"]: color for var, color in zip(selected_variables, px.colors.qualitative.Dark24)}
                    color_map[name_prediction] = 'black'  # Color fijo para la predicción

                    # Asegurarse de que y_axes y y_axis_labels incluyan la predicción
                    if name_prediction not in y_axes:
                        y_axes[name_prediction] = f"y{len(y_axes) + 1}"
                        y_axis_labels[y_axes[name_prediction]] = name_prediction.capitalize()

                    #  Agregar línea de predicción
                    if name_prediction in data_prediction:
                        fig.add_trace(go.Scatter(
                            x=data_prediction["_time"], 
                            y=data_prediction[name_prediction], 
                            mode="lines",
                            name=name_prediction.capitalize(),
                            yaxis=y_axes[name_prediction],
                            line=dict(color=color_map[name_prediction], dash="dash")  # Estilo predicción
                        ))

                    # Agregar líneas de las variables seleccionadas
                    for var in selected_variables:
                        var_name = var["variable_name"]
                        if var_name in data_prediction:
                            if var_name not in y_axes:
                                y_axes[var_name] = f"y{len(y_axes) + 1}"
                                y_axis_labels[y_axes[var_name]] = var_name.capitalize()

                            fig.add_trace(go.Scatter(
                                x=data_prediction["_time"], 
                                y=data_prediction[var_name], 
                                mode="lines",
                                name=var_name.capitalize(),
                                yaxis=y_axes[var_name],
                                line=dict(color=color_map[var_name])
                            ))

                    # Crear configuración dinámica de ejes
                    trace_colors = {axis: color_map[var] for var, axis in y_axes.items() if var in color_map}

                    layout_yaxes = {}
                    for i, (axis, color) in enumerate(trace_colors.items(), start=1):
                        layout_yaxes[axis] = {
                            'title': y_axis_labels[axis],
                            'title_font': dict(color=color),
                            'side': 'left' if i == 1 else 'right',
                            'position': 1 - (0.10 * (i - 2)) if i > 1 else None,
                            'overlaying': 'y' if i > 1 else None,
                            'tickfont': dict(color=color)
                        }

                    layout_update = {f'yaxis{i}': layout_yaxes.get(f'y{i}', {}) for i in range(1, len(y_axes) + 1)}

                    # 6️⃣ Configurar layout final
                    fig.update_layout(
                        title="Performance Penicillin",
                        xaxis_title="Time",
                        yaxis_title="Penicillin",
                        xaxis=dict(tickangle=-45),
                        legend=dict(
                            orientation="h",
                            yanchor="top",
                            y=-0.2,
                            xanchor="center",
                            x=0.5
                        ),
                        hovermode="x unified",
                        **layout_update
                    )
                    
                inicio_pred += 1

            return fig, data_prediction

@dash.callback(
    Output('slider-value-output', 'children'),
    Output('interval-component', 'interval'),
    Input('interval-seconds-input', 'value')
)
def update_interval_display(seconds):
    return f"Interval update (seconds): {seconds}", seconds * 1000