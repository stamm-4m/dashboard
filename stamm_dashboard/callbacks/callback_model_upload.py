import dash
from dash import html, Input, Output, State, ALL
import base64
import yaml
import os
import dash_bootstrap_components as dbc

upload_id="upload-data"
output_id="output-data-upload"
allowed_extensions = ["pkl", "yaml", "rds"]

# Create the storage folder if it does not exist
upload_folder = "../ML_Repository"
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)


@dash.callback(
            Output("dynamic-feature-container", "children"),
            Output("feature-store", "data",allow_duplicate=True),
            Input("add-feature-button", "n_clicks"),
            State("feature-store", "data"),
            prevent_initial_call=True
)
def add_feature(feature_store):
    """Agrega una nueva característica al formulario."""
            if feature_store is None:
                feature_store = []

            # Agregar una nueva característica vacía al almacén
            feature_store.append({
                "name": "",
                "type": "",
                "description": "",
                "units": "",
                "lag": 0
            })

            # Renderizar todos los campos dinámicos basados en el almacén
            feature_inputs = []
            for idx, feature in enumerate(feature_store):
                feature_inputs.append(
                    dbc.Row([
                        dbc.Col([
                            dbc.Label(f"Feature Name {idx + 1}:"),
                            dbc.Input(id={"type": "feature-name", "index": idx}, type="text", value=feature["name"], placeholder="Feature name"),
                            dbc.Label("Type:"),
                            dbc.Input(id={"type": "feature-type", "index": idx}, type="text", value=feature["type"], placeholder="Type"),
                            dbc.Label("Description:"),
                            dbc.Input(id={"type": "feature-description", "index": idx}, type="text", value=feature["description"], placeholder="Description"),
                            dbc.Label("Units:"),
                            dbc.Input(id={"type": "feature-units", "index": idx}, type="text", value=feature["units"], placeholder="Units"),
                            dbc.Label("Lag:"),
                            dbc.Input(id={"type": "feature-lag", "index": idx}, type="number", value=feature["lag"], placeholder="Lag"),
                        ], md=6)
                    ], className="mb-4")
                )

            return feature_inputs, feature_store

@dash.callback(
            Output("feature-store", "data",allow_duplicate=True),
            Input({"type": "feature-name", "index": ALL}, "value"),
            Input({"type": "feature-type", "index": ALL}, "value"),
            Input({"type": "feature-description", "index": ALL}, "value"),
            Input({"type": "feature-units", "index": ALL}, "value"),
            Input({"type": "feature-lag", "index": ALL}, "value"),
            State("feature-store", "data"),
            prevent_initial_call=True
)
def update_feature_store(names, types, descriptions, units, lags, feature_store):
            """Actualiza el almacén con los valores dinámicos."""
            for idx, feature in enumerate(feature_store):
                feature["name"] = names[idx]
                feature["type"] = types[idx]
                feature["description"] = descriptions[idx]
                feature["units"] = units[idx]
                feature["lag"] = lags[idx]

            return feature_store


        
        # Callback para subir el archivo 
@dash.callback(
            Output(output_id, 'children', allow_duplicate=True),
            Input(upload_id, 'contents'),
            State(upload_id, 'filename'),
            prevent_initial_call=True
)
def update_output(contents, filename):
            if contents is None or filename is None:
                return html.Div(["No file has been uploaded."])

            # Valida las extenciones permitidas
            extension = filename.split('.')[-1].lower()
            if extension not in allowed_extensions:
                return html.Div(["File type not allowed. Only allowed types are: " + ", ".join(allowed_extensions)])

            # Decode the uploaded file
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                # Guardar el archivo en la carpeta "Models" 
                filepath = os.path.join(upload_folder, filename)
                with open(filepath, "wb") as f:
                    f.write(decoded)

                return html.Div([
                    html.P(f"File {filename} uploaded successfully."),
                ])
            except Exception as e:
                return html.Div([
                    html.P("Error processing the file."),
                    html.P(str(e))
                ])
        # Callback para guardar la información adicional en un archivo YAML
@dash.callback(
            Output("output-data-upload", "children", allow_duplicate=True),
            Input("save-ml-model-config", "n_clicks"),
            [
                State("model_name", "value"),
                State("model_type", "value"),
                State("language", "value"),
                State("model_file", "value"),
                State("package_name", "value"),
                State("model_class", "value"),
                State("number_of_instances", "value"),
                State("sampling_rate", "value"),
                State("number_of_trees", "value"),
                State("max_tree_depth", "value"),
                State("db_info", "value"),
                State("validation", "value"),
                State("feature-store", "data"),  # Se leen las características del Store
                State("prediction_name", "value"),
                State("prediction_description", "value"),
                State("prediction_units", "value"),
                State("forecast_horizon", "value"),
                State(upload_id, "filename")
            ],
            prevent_initial_call=True
        )
def save_metadata(
            n_clicks, model_name, model_type, language, model_file, package_name, model_class,
            number_of_instances, sampling_rate, number_of_trees, max_tree_depth, db_info,
            validation, features, prediction_name, prediction_description, prediction_units,
            forecast_horizon, filename
        ):
            if n_clicks is None or filename is None:
                return html.Div()

            print("FEATURES:", features)  # Depuración
            # Procesar las características correctamente
            formatted_features = [
                {
                    "name": f["name"],
                    "type": f["type"],
                    "description": f["description"],
                    "units": f["units"],
                    "lag": f["lag"]
                } for f in features if f  # Asegurarse de que no haya características vacías
            ]

            # Crear el diccionario del YAML
            yaml_data = {
                "ml_model_configuration": {
                    "model_description": {
                        "model_name": model_name,
                        "model_type": model_type,
                        "language": language,
                        "config_files": {
                            "model_file": model_file
                        },
                        "packages": {
                            "package": [
                                {"name": package_name},
                                {"class": model_class}
                            ]
                        },
                        "number_of_instances": number_of_instances,
                        "sampling_rate": sampling_rate,
                        "hyperparameters": {
                            "number_of_trees": number_of_trees,
                            "max_tree_depth": max_tree_depth
                        },
                        "db_info": db_info,
                        "validation": validation
                    },
                    "inputs": {
                        "features": formatted_features
                    },
                    "outputs": {
                        "predictions": [
                            {
                                "name": prediction_name,
                                "description": prediction_description,
                                "units": prediction_units,
                                "forecast_horizon": forecast_horizon
                            }
                        ]
                    }
                }
            }

            # Guardar el archivo YAML
            yaml_filepath = os.path.join(upload_folder, f"{filename}.yaml")
            with open(yaml_filepath, "w") as yaml_file:
                yaml.dump(yaml_data, yaml_file, default_flow_style=False)

            return html.Div([
                html.P("Configuration saved successfully."),
                html.P(f"YAML file path: {yaml_filepath}")
            ])