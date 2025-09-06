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
                    dbc.Container([
                        dbc.Row([
                            # Columna para el Label y Dropdown con Loading
                            dbc.Col(
                                [
                                    dbc.Label("Model Name:", className="mb-2"),
                                    dcc.Loading(
                                        id="loading-models",
                                        type="circle",
                                        color="#0d6efd",  # Azul Bootstrap
                                        fullscreen=False,
                                        children=dcc.Dropdown(
                                            id='model-selector-off',
                                            options=model_name_options,
                                            placeholder="Select a model",
                                            className="shadow-sm",
                                            style={
                                                'width': '100%',
                                                'minWidth': '280px',  # Ancho mínimo elegante
                                                'height': '42px',     # Ajusta altura
                                                
                                            }
                                        )
                                    )
                                ],
                                md=7,
                                className="d-flex flex-column"
                            ),
                            # Columna para el botón
                            dbc.Col(
                                [
                                    dbc.Button(
                                        "Show Simulation",
                                        id="run",
                                        n_clicks=0,
                                        color="primary",
                                        size="lg",  # Botón grande
                                        className="shadow-sm w-100",  # Igual ancho que dropdown
                                    )
                                ],
                                md=5,
                                className="d-flex align-items-end"
                            ),
                        ], className="g-3"),  # Espacio entre columnas
                        dbc.Row([
                            dbc.Col(html.Div(id='model-details-off',className="mt-5"), width=12)
                        ]),
                    ], fluid=True),
                ]),
                className="my-3 shadow-sm rounded-4 p-3"
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