from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from utils import model_selector
from utils.utils_global import disabled_figure


def softsensor_online_layout():
        model_name_options = model_selector.get_model_name_options()
        
        return html.Div([
            # Title
            html.H2("Soft sensors Online", className="text-center my-5"),
            # Card container
            dbc.Card(
                dbc.CardBody([
                    # Additional form for file information
                    dbc.Container([
                        # General model information section
                        dbc.Row([
                            # Column for model description (centered text)
                            dbc.Col(
                                [
                                    dbc.Label("Model Name:"),
                                    dcc.Dropdown(
                                        id='model-selector',
                                        options=model_name_options,
                                        placeholder="Select a model",
                                        style={
                                            'width': '100%',
                                            'marginBottom': '20px',
                                            'height': '38px',  # Ensure consistent height with button
                                            'lineHeight': '1.5',  # Adjust internal text alignment
                                        }
                                    )
                                ],
                                md=7,  # Each column takes up 1/4 of the row
                                className="d-flex flex-column align-items-center"
                            ),
                            # Column for action button
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Run",
                                        id="run-on",
                                        n_clicks=0,
                                        color="primary",
                                        style={
                                            'width': '60%',
                                        },
                                    )
                                ],
                                md=5,  # Each column takes up 1/4 of the row
                                className="d-flex justify-content-center mt-2",  # Center vertically
                            ),
                        ],
                        className="align-items-center"),
                        # Row for model details
                        dbc.Row(
                            dbc.Col(
                                html.Div(id='model-details'),
                                width=12
                            )
                        ),
                    ],
                    fluid=True),
                ]),
                className="my-3 shadow-sm",
            ),
            dbc.Card(
                dbc.CardBody([
                    dbc.Container([
                        # Row for graphic controls
                        dbc.Row(
                        [
                            # Column for variable type and name selection
                            dbc.Col(
                                [
                                    # Variable type selector
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Variable:", html_for="type-selector", className="mb-1"),
                                                width=3  # Width for the label
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='type-selector',
                                                    options=[],
                                                    placeholder="Select a type",
                                                    style={
                                                        'width': '100%',
                                                        'height': '38px',  # Consistent height with button
                                                        'lineHeight': '1.5',  # Adjust internal text alignment
                                                    }
                                                ),
                                                width=9  # Width for the input
                                            ),
                                        ],
                                        className="mb-3"
                                    ),
                                    # Variable name selector
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Name:", html_for="name-selector", className="mb-1"),
                                                width=3  # Width for the label
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='name-selector',
                                                    options=[],
                                                    placeholder="Select a name",
                                                    style={
                                                        'width': '100%',
                                                        'height': '38px',  # Consistent height with button
                                                        'lineHeight': '1.5',  # Adjust internal text alignment
                                                    }
                                                ),
                                                width=9  # Width for the input
                                            ),
                                        ],
                                        className="mb-3"
                                    ),
                                    # Add Variable Button
                                    dbc.Row(
                                        dbc.Col(
                                            dbc.Button(
                                                "Add Variable",
                                                id='add-variable-btn',
                                                color="primary",
                                                className="w-50"  # Button width
                                            ),
                                            className="d-flex justify-content-center mt-3"  # Center the button
                                        )
                                    ),
                                ],
                                md=6,  # Column width adjusted to take up half of the row
                                className="d-flex flex-column"
                            )
                            ,
                            # Column for view control
                            dbc.Col(
                                [html.Table(id="variable-table", className="table"),
                                dbc.Alert(id="msj-div", is_open=False, color="info", dismissable=True),
                                dcc.Store(id="variable-data-store", data=[])],
                            md=6,  # Column width adjusted to take up the remaining half
                                className="d-flex justify-content-center"
                            )
                        ],
                        className="align-items-center"  # Ensures vertical alignment of the row contents
                    ),
                        # Row display experiment-id
                        dbc.Row(
                            dbc.Col(
                                html.Div(
                                    html.H5(id="experiment-id-display-on", className="mt-4 mb-4 text-center"),
                                    className="d-flex justify-content-center"
                                )
                            )
                        ),
                        # Row Graphic to prediction
                        dbc.Row(
                            dbc.Col(
                                [
                                    html.Div(className='row', children=[
                                        html.Div(id='msj-div'),
                                        html.Div(id='dd-output-container'),
                                        html.Div(className='twelve columns', children=[
                                            dcc.Graph(
                                                id='line-chart-prediction-on',
                                                figure=disabled_figure
                                            ),
                                            # Store data between updates
                                            dcc.Store(id="prediction-data", data={"_time": [], "penicillin_concentration": [], "var1": [],"var2": [],"var3": []}),
                                            dcc.Store(id="selected-variables", data=[{"variable_name":"penicillin_concentration"}]),
                                            dcc.Interval(
                                                id='interval-component',
                                                interval=10000,  # in milliseconds
                                                n_intervals=0
                                            )
                                        ])
                                    ])
                                ]
                            )
                        )
                    ])
                ]),
                className="my-3 shadow-sm",
            )
        ])


    
        

   
        