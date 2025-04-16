from dash import dcc, html
import dash_bootstrap_components as dbc
from ..callbacks.callback_model_upload import upload_id,output_id


   
def model_upload_layout():
        """Property that generates the layout for the upload component and additional form."""
        return html.Div([
            html.H2("ML File Management Panel", className="text-center my-4"),
            # Section: Upload File
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H3("Upload Model"),
                        dcc.Upload(
                            id=upload_id,
                            children=html.Button('Upload'),
                            multiple=False
                        )
                    ]
                ),
                className="my-3 shadow-sm",
            ),
            html.Div(id=output_id),
            dbc.Card(
                dbc.CardBody(
                    [
                        # Additional form for file information
                        dbc.Container([
                            # General model information
                            dbc.Row([
                                dbc.Col([
                                    html.H4("Model Description", className="mb-3"),
                                    dbc.Label("Model Name:"),
                                    dbc.Input(id="model_name", type="text", placeholder="random_forest"),
                                    dbc.Label("Model Type:"),
                                    dbc.Input(id="model_type", type="text", placeholder="interpretable"),
                                    dbc.Label("Language:"),
                                    dbc.Input(id="language", type="text", placeholder="python"),
                                    dbc.Label("Model Configuration File:"),
                                    dbc.Input(id="model_file", type="text", placeholder="0001_[python]_penicillin_RF.pkl"),
                                ], md=6),
                                dbc.Col([
                                    html.H4("Packages", className="mb-3"),
                                    dbc.Label("Package Name:"),
                                    dbc.Input(id="package_name", type="text", placeholder="sklearn.ensemble"),
                                    dbc.Label("Model Class:"),
                                    dbc.Input(id="model_class", type="text", placeholder="RandomForestRegressor"),
                                ], md=6)
                            ], className="mb-4"),

                            # Number of instances and sampling rate
                            dbc.Row([
                                dbc.Col([
                                    html.H4("General Parameters", className="mb-3"),
                                    dbc.Label("Number of Instances:"),
                                    dbc.Input(id="number_of_instances", type="number", placeholder="89800"),
                                    dbc.Label("Sampling Rate:"),
                                    dbc.Input(id="sampling_rate", type="text", placeholder="1 measurement/[12][min]"),
                                ], md=6),
                                dbc.Col([
                                    html.H4("Hyperparameters", className="mb-3"),
                                    dbc.Label("Number of Trees:"),
                                    dbc.Input(id="number_of_trees", type="number", placeholder="5"),
                                    dbc.Label("Max Tree Depth:"),
                                    dbc.Input(id="max_tree_depth", type="number", placeholder="7"),
                                ], md=6)
                            ], className="mb-4"),

                            # Additional information
                            dbc.Row([
                                dbc.Col([
                                    html.H4("Additional Information", className="mb-3"),
                                    dbc.Label("Database Configuration Path:"),
                                    dbc.Input(id="db_info", type="text", placeholder="../DB/db_penicillin.yaml"),
                                    dbc.Label("Validation:"),
                                    dbc.Input(id="validation", type="text", placeholder="10-fold CV - 3 repetitions"),
                                ], md=6),
                            ], className="mb-4"),

                            # Input Features
                            html.Div([
                                html.H4("Input Features", className="my-4"),
                                html.Button("Add Feature", id="add-feature-button", n_clicks=0, className="btn btn-primary mb-3"),
                                html.Div(id="dynamic-feature-container", children=[]),
                                dcc.Store(id="feature-store", data=[])  # Store to maintain features
                            ]),

                            # Output Predictions
                            html.H4("Output Predictions", className="my-4"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Prediction Name:"),
                                    dbc.Input(id="prediction_name", type="text", placeholder="penicillin_concentration"),
                                    dbc.Label("Prediction Description:"),
                                    dbc.Input(id="prediction_description", type="text", placeholder="Prediction of the penicillin concentration."),
                                    dbc.Label("Prediction Units:"),
                                    dbc.Input(id="prediction_units", type="text", placeholder="g L−1"),
                                    dbc.Label("Forecast Horizon:"),
                                    dbc.Input(id="forecast_horizon", type="number", placeholder="0"),
                                ], md=6)
                            ]),

                            # Save button
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("Save Configuration", id="save-ml-model-config", color="primary", className="mt-4"),
                                ], className="text-center")
                            ])

                        ], fluid=True),
                    ]
                ),
                className="my-3 shadow-sm",
            ),
        ])
    
    
        

