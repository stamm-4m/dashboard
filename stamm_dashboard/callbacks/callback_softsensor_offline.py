import dash
from dash import Input, Output, State, html,ALL,ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate
from ..utils import model_selector
from ..InfluxDb import influxdb_handler # recuperamos la instancia creada
from ..utils.utils_sofsensors_offline import reload_models_yaml, generate_predictions, generate_prediction_name #se cargan las fuciones utils necesarias para los callback
from ..pages.model_details_view import generate_model_details_view
import pandas as pd
import plotly.express as px


#Control inicio prediccion
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
            Elimina solo la traza de la variable correspondiente cuando se presiona su botón de eliminación.
            """
            if not any(n_clicks):  # Si no se ha presionado ningún botón, no hacer nada
                raise PreventUpdate  

            if not current_figure or "data" not in current_figure:
                raise PreventUpdate  # Evita errores si la figura está vacía

            fig = go.Figure(current_figure)  # Mantenemos la figura original

            # Identificar qué botones fueron presionados
            clicked_indices = [i for i, click in enumerate(n_clicks) if click]

            if not clicked_indices or not selected_variables:
                raise PreventUpdate  

            # Variables a eliminar
            variables_to_remove = set(
                selected_variables[i]["variable_name"]
                for i in clicked_indices
                if i < len(selected_variables) and "variable_name" in selected_variables[i]
            )

            print(f"❌ Eliminando variables de la gráfica: {variables_to_remove}")

            # Filtrar las trazas y eliminar solo las necesarias
            fig.data = tuple(trace for trace in fig.data if trace.name not in variables_to_remove)

            print(f"📉 Gráfico actualizado. Variables restantes: {[trace.name for trace in fig.data]}")

            return fig

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
                return model_selector.get_names_by_category(selected_category,model_name)
            else:
                # Return an empty list if no category is selected
                return []
        # Function to update the options of the existing models
@dash.callback(
            Output('model-selector-off', 'options'),
            Input('model-selector-off', 'n_clicks')
        )
def update_model_options(n_clicks):
            reload_models_yaml()
            return model_selector.get_model_name_options()
        
        # Function to update the ypes  of model inputs
@dash.callback(
            Output('type-selector-on', 'options'),
            Input('model-selector-off', 'value'),
            prevent_initial_call=True
        )
def update_model_types(name):
            #print("name",name)
            types_variable = model_selector.get_unique_types_models(name)
            #print("types_variable",types_variable)
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
        # Callback para inicializar la predicción
@dash.callback(
            Output("line-chart-prediction-off", "figure"),  # Gráfica donde se añadirán las nuevas variables
            Input("add-variable-btn", "n_clicks"),  # Botón para agregar variables
            Input("selected-variables-off", "data"),  # Variables seleccionadas por el usuario
            State("line-chart-prediction-off", "figure"),  # Estado actual de la gráfica
            prevent_initial_call=True  # Evita ejecución automática
        )
def update_graph_var(n_clicks, selected_variables, current_figure):
            global dfc

            print(f"🔄 Callback ejecutado - Clicks: {n_clicks}, Variables seleccionadas: {selected_variables}")

            if not selected_variables:
                print("⚠ No hay variables seleccionadas. No se actualizará la gráfica.")
                return go.Figure(current_figure) if current_figure else go.Figure()

            if dfc is None or "_time" not in dfc:
                print("⚠ No hay datos en dfc o falta la columna '_time'.")
                return go.Figure(current_figure) if current_figure else go.Figure()

            df = pd.DataFrame(dfc)
            df["_time"] = pd.to_datetime(df["_time"], errors="coerce")

            fig = go.Figure(current_figure) if current_figure else go.Figure()

            existing_traces = {trace.name for trace in fig.data}
            print(f"📊 Variables ya graficadas: {existing_traces}")

            colors = px.colors.qualitative.Dark24  

            # Identificar ejes Y existentes en el layout
            existing_y_axes = {k for k in fig.layout if k.startswith("yaxis")}
            num_existing_y_axes = len(existing_y_axes)

            # Iterar sobre cada variable seleccionada y agregarla si no está graficada
            for i, var_data in enumerate(selected_variables):
                if not isinstance(var_data, dict) or "variable_name" not in var_data:
                    print(f"⚠ Formato inesperado en selected_variables[{i}]: {var_data}")
                    continue

                var = var_data["variable_name"]

                if var in df.columns and var not in existing_traces:
                    color = colors[num_existing_y_axes % len(colors)]  
                    y_axis_name = f"yaxis{num_existing_y_axes + 1}"  # yaxis2, yaxis3, etc.
                    y_axis_ref = f"y{num_existing_y_axes + 1}"  # y2, y3, etc.

                    # Agregar traza con su propio eje Y
                    fig.add_trace(go.Scatter(
                        x=df["_time"].astype(str),
                        y=df[var],
                        mode="lines",
                        name=var,
                        yaxis=y_axis_ref,  
                        line=dict(color=color)
                        
                    ))

                    # Agregar nuevo eje Y al layout
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

                    print(f"✅ Variable '{var}' agregada con eje {y_axis_ref}.")

                else:
                    print(f"⚠ Variable '{var}' ya está graficada o no existe en los datos.")

            # Configurar layout general del gráfico
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

            print(f"📊 Gráfico actualizado con {len(fig.data)} variables y múltiples ejes Y.")

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
            # Obtener los datos para el batch seleccionado
            dfc = influxdb_handler.get_data_by_batch_id2(store_data['selected_experiment'])
            inicio_pred += 1  # Reiniciar el contador de predicciones
            txt_prediction = generate_prediction_name("default_model.pkl")
           
            if "model_file" in data_model and data_model["model_file"]:
                txt_prediction = generate_prediction_name(data_model["model_file"])
            print("txt_prediction:",txt_prediction)
            

            print(f"🔄 Callback ejecutado - Intervalo: {n}, Inicio_pred: {inicio_pred}")

            fig = go.Figure()

            if n > 0 and inicio_pred > 0:
                predicted_values = generate_predictions(store_data['selected_experiment'], data_model, inicio_pred)

                if predicted_values is None or predicted_values.empty:
                    print("⚠ No hay datos en predicted_values.")
                    return fig, {"_time": [], txt_prediction: []}

                print(f"✅ {len(predicted_values)} registros obtenidos para predicción.")

                # Convertimos `_time` a datetime y luego a str
                predicted_values["_time"] = pd.to_datetime(predicted_values["_time"], errors="coerce").astype(str)
                
                if predicted_values["_time"].isnull().all():
                    print("⚠ Error: Todos los valores de `_time` son nulos. No se puede graficar.")
                    return fig, {"_time": [], txt_prediction: []}

                # Crear estructura para almacenar los datos
                data_prediction = {
                    "_time": predicted_values["_time"].tolist(),
                    txt_prediction: []
                }

                # 🔹 Validar si `txt_prediction` existe en los datos
                predicted_values.columns = predicted_values.columns.str.strip()  # Eliminar espacios en nombres de columnas
                column_data = predicted_values.get(txt_prediction)

                if column_data is not None:
                    data_prediction[txt_prediction] = column_data.tolist()
                    print(f"📈 Se encontró '{txt_prediction}' en los datos. Primeros 5 valores:", data_prediction[txt_prediction][:5])

                    # Verificar que haya valores numéricos en `y`
                    if not any(pd.notna(data_prediction[txt_prediction])):
                        print("⚠ Error: Todos los valores de `penicillin_concentration` son nulos.")
                        return fig, data_prediction

                    # Convertir `_time` nuevamente a datetime para graficar correctamente
                    data_prediction["_time"] = pd.to_datetime(data_prediction["_time"])

                    # Agregar la traza al gráfico
                    fig.add_trace(go.Scatter(
                        x=data_prediction["_time"].astype(str),
                        y=data_prediction[txt_prediction],
                        mode="lines",
                        name="Penicillin Concentration",
                        yaxis="y",
                        line=dict(color="blue")
                    ))

                    # Configurar layout del gráfico
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
                    print(f"⚠ No se encontró '{txt_prediction}' en los datos.")

                inicio_pred += 1

            print(f"📊 Número de trazas en la gráfica al final: {len(fig.data)}")
            #plot = ui.plotly(fig).classes('w-full h-40')
            #plot = fig.to_dict()
            return fig, data_prediction
