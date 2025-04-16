import dash
from dash import Input, Output, State, html,ALL,ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from ..utils import model_selector
from ..InfluxDb import influxdb_handler # recuperamos la instancia creada
from ..utils.utils_sofsensors_offline import reload_models_yaml
from ..utils.utils_softsensors_online import create_toast,generate_predictions
from ..pages.model_details_view import generate_model_details_view
import pandas as pd
import plotly.express as px
from utils.utils_global import disabled_figure


#Control inicio prediccion
inicio_pred = 0
dfc = pd.DataFrame()


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
                ]) for i, variable in enumerate(current_data[1:])
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
                return model_selector.get_names_by_category(selected_category,model_name)
            else:
                # Return an empty list if no category is selected
                return []
        # Function to update the options of the existing models
@dash.callback(
            Output('model-selector', 'options'),
            Input('model-selector', 'n_clicks')
        )
def update_model_options(n_clicks):
            reload_models_yaml()
            return model_selector.get_model_name_options()
        
        # Function to update the ypes  of model inputs
@dash.callback(
            Output('type-selector', 'options'),
            Input('model-selector', 'value'),
            prevent_initial_call=True
        )
def update_model_types(name):
            #print("name",name)
            types_variable = model_selector.get_unique_types_models(name)
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

            config = model_selector.get_configuration_by_model_name_language(selected_model)

            if config:
                model_data = {
                    "model_file": config['ml_model_configuration']['model_description'].get('config_files', {}).get('model_file', 'N/A'),
                    "model_name": config['ml_model_configuration']['model_description'].get('model_name', 'N/A'),
                    "language": config['ml_model_configuration']['model_description'].get('language', 'N/A'),
                    "predictions": config['ml_model_configuration']['outputs']['predictions'],
                    "features": config['ml_model_configuration']['inputs']['features']
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
            State("selected-variables", "data"),
            Input(component_id='run-on', component_property='n_clicks'),
            prevent_initial_call='initial_duplicate'
        )
def update_graph(data_model, store_data, n,data_prediction, selected_variables,n_clicks):
            global  inicio_pred, dfc
            if n_clicks == 0:
                # # Obtener los datos para el batch seleccionado
                if store_data is None or 'selected_experiment' not in store_data:
                    return (disabled_figure, None)  
                
                dfc = influxdb_handler.get_data_by_batch_id2(store_data['selected_experiment']) 
                inicio_pred += 1  # Reiniciar el contador de predicciones
                print(f"Initial figure data: fig")  # Verificar los datos en la figura
           
            fig = go.Figure()

            # Inicializar los diccionarios vacíos
            y_axes = {}
            y_axis_labels = {}
            if n > 0 and inicio_pred > 0 and "model_file" in data_model and data_model["model_file"]:
               
                # Generar predicciones de penicilina    
                predicted_values = generate_predictions(store_data['selected_experiment'], data_model, inicio_pred)

                print(f"predicted_values: {predicted_values}")  # Verificar las predicciones

                if predicted_values is not None and not predicted_values.empty:
                    
                    tiempo_pred = pd.to_datetime(predicted_values['_time'])  # Asegurar que el tiempo es datetime
                    nivel_pred = predicted_values['penicillin_concentration']
                    print("predicted_values: ",predicted_values)
                    print(f"Actualizando predicción: {tiempo_pred}, {nivel_pred}")  # Ver predicción
                    # Agregar nuevos datos al almacenamiento
                    data_prediction["_time"].append(tiempo_pred.strftime("%Y-%m-%d %H:%M:%S"))
                    data_prediction["penicillin_concentration"].append(nivel_pred)

                    # Obtener valores de las variables
                    #  Procesar los datos de las variables
                    i = 1
                    for variable in selected_variables:
                        var_name = variable["variable_name"]
                        axis = f"y{i}"  # Crear el nombre del eje, como "y", "y2", etc.
                        # Asignar la variable y el nombre de la etiqueta al diccionario
                        y_axes[var_name] = axis
                        y_axis_labels[axis] = var_name.capitalize()
                        i=i+1
                        if(variable["variable_name"] != "penicillin_concentration"):
                            value_variable = predicted_values.get(variable["variable_name"])
                            if value_variable is None:
                                selected_variables = [var for var in selected_variables if var["variable_name"] in predicted_values]
                                create_toast(f"Warning: The variable '{variable['variable_name']}' is not part of the model.")
                            else:
                                # Continúa con el procesamiento si la variable está presente
                                if pd.isna(value_variable):
                                    print(f"Datos de la variable {variable['variable_name']}: {value_variable}")
                                else:
                                    if variable["variable_name"] not in data_prediction:
                                        data_prediction[variable["variable_name"]] = []  # Crear la clave con una lista vacía
                                    
                                    data_prediction[variable["variable_name"]].append(value_variable)
                                    print(f"Datos de la variable {variable['variable_name']}: {value_variable}")
                    # Diccionario para almacenar los colores de cada variable
                    color_map = {var["variable_name"]: color for var, color in zip(selected_variables, px.colors.qualitative.Dark24)}

                    for var in selected_variables:
                        
                        if var["variable_name"] in data_prediction:
                            fig.add_trace(go.Scatter(
                                x=data_prediction["_time"], 
                                y=data_prediction[var["variable_name"]], 
                                mode="lines",
                                name=var["variable_name"].capitalize(),
                                yaxis=y_axes[var["variable_name"]],
                                line=dict(color=color_map[var["variable_name"]])
                            ))

                    # Crear diccionario `trace_colors` basado en `color_map`
                    trace_colors = {y_axes[var["variable_name"]]: color_map[var["variable_name"]] for var in selected_variables}

                    # Configuración dinámica de los ejes en layout con los colores detectados
                    layout_yaxes = {}
                    for i, (axis, color) in enumerate(trace_colors.items(), start=1):
                        layout_yaxes[axis] = {
                            'title': y_axis_labels[axis],  # Título como string
                            'title_font': dict(color=color),  # Color del título
                            'side': 'left' if i == 1 else 'right',
                            'position': 1 - (0.10 * (i - 2)) if i > 1 else None,
                            'overlaying': 'y' if i > 1 else None,
                            'tickfont': dict(color=color)  # Aplicar color a los ticks
                        }    
                    # Actualizar el layout de la figura con los ejes configurados
                    layout_update = {}
                    for i in range(1, len(y_axes) + 1):
                        layout_update[f'yaxis{i}'] = layout_yaxes.get(f'y{i}', {})

                    # Configuración del layout
                    fig.update_layout(
                        title="Performance Penicilin",
                        xaxis_title="Time",
                        yaxis_title="Penicillin",
                        xaxis=dict(
                            tickangle=-45  # Inclinar etiquetas para mejor visibilidad
                        ),
                        legend=dict(
                        orientation="h",  # Leyenda en horizontal
                        yanchor="top",    # Anclar en la parte superior de la leyenda
                        y=-0.2,           # Mover la leyenda debajo de la gráfica
                        xanchor="center",
                        x=0.5             # Centrar la leyenda
                        ),
                        **layout_update
                    )
                    
                inicio_pred += 1

            return fig, data_prediction
