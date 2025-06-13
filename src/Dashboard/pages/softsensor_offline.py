from dash import html, dcc
import dash_bootstrap_components as dbc

from Dashboard.utils import model_information
from Dashboard.utils.utils_global import disabled_figure



def sofsensor_offline_layout():
        model_name_options = model_information.get_model_name_options()
        
        return html.Div([
            # Title
            html.H2("Soft sensors Offline", className="text-center my-2"),
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
                                        id='model-selector-off',
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
                                        "Show simulation",
                                        id="run",
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
                                html.Div(id='model-details-off'),
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
                                                dbc.Label("Variable:", html_for="type-selector-on", className="mb-1"),
                                                width=3  # Width for the label
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='type-selector-on',
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
                                                dbc.Label("Name:", html_for="name-selector-off", className="mb-1"),
                                                width=3  # Width for the label
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='name-selector-off',
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
                                [html.Table(id="variable-table-off", className="table"),
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
                                    html.H5(id="experiment-id-display-off", className="mt-4 mb-4 text-center"),
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
                                                id='line-chart-prediction-off', figure=disabled_figure
                                            ),
                                            # Store data between updates
                                            dcc.Store(id="prediction-data-off", data={}),
                                            dcc.Store(id="selected-variables-off", data=[]),
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