import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from utils.utils_global import disabled_figure
from utils import model_information

def maintenance_layout():

    # Load model options dynamically for layout
    model_options = model_information.get_model_name_options()
    print("model_options view:",model_options)

    # Return only the content specific to the maintenance page
    return html.Div([
            html.H3("Simulation Assessment", className="mb-4"),

            # Sección de entrada
            html.Div([
            
            dbc.Row([
                dbc.Col(
                        html.Div([
                            html.Label("Selected experiment ID:"),
                            html.Br(),
                            html.Label(id="experiment-id-display-maintenence"),
                            ])
                    )
            ], className="mb-2"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Model Name:"),
                    dcc.Dropdown(
                        id='model-selector-maintenance',
                        options=model_options,
                        placeholder="Select a model",
                        style={'width': '100%', 'marginBottom': '10px'}
                    )
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Time range selection:"),
                    dcc.RangeSlider(
                        id="time-window-slider",
                        min=0,
                        max=0,
                        step=1,
                        marks=None,
                        value=[0, 100],
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True,
                            "style": {"color": "LightSteelBlue", "fontSize": "20px"},
                        }
                    ),
                    html.Div(id="time-slider-labels", style={"textAlign": "center", "marginBottom": "20px"})
                ], width=12),
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Variable Type:"),
                    dcc.Dropdown(id='type-selector-maintenance', options=[], placeholder="Select a type", style={'width': '100%'})
                ], width=6),
                dbc.Col([
                    dbc.Label("Variable Name:"),
                    dcc.Dropdown(id='name-selector-maintenance', options=[], placeholder="Select a name", style={'width': '100%'})
                ], width=6),
            ], className="mb-2"),
            dbc.Row([
                dbc.Col(dbc.Button("Add Variable", id="add-variable-btn-maintenance", color="primary", className="w-100"), width=12)
            ], className="mt-2"),
            dcc.Store(id="variable-store-maintenance", data=[])
        ]),

        # Tabla
        html.Div([
            html.Table(id="variable-table-maintenance", className="table")
        ], className="mt-4"),

        # Gráfico
        dcc.Graph(id="maintenance-graph", figure=disabled_figure, className="mt-4"),
        # Tabla debajo del gráfico
        dash_table.DataTable(
            id="prediction-table",
            columns=[],  # se rellenan dinámicamente
            data=[],     # también se llena dinámicamente
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            row_selectable="single",  # permite seleccionar solo una fila
            selected_rows=[],
            page_size=10
        ),
        dcc.Store(id="selected-variables-maintenance", data=[]),
        dbc.Row([
            dbc.Col(html.Div(id="save-confirmation", className="text-success"),width=12)
        ], className="mt-4"),
        # Botones de acción
        dbc.Row([
            dbc.Col(dbc.Button("Save Simulation", id="save-table-btn", color="success", className="w-100"), width=12)
            #dbc.Col(dbc.Button("Set Maintenance", id="maintain-model", color="danger", className="w-100"), width=6)
        ], className="mt-4"),

        # Componente de descarga
        dcc.Download(id="download-excel"),

        # Modal: Save simulation
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Confirm save")),
            dbc.ModalBody([
                html.P("Do you want to save the changes to the table?"),
                # 🔽 Dropdown de Nivel
                html.Label("Level", className="mt-2"),
                dcc.Dropdown(
                    id="dropdown-nivel",
                    options=[
                        {"label": "low", "value": "low"},
                        {"label": "Medium", "value": "medium"},
                        {"label": "Hight", "value": "hight"},
                    ],
                    placeholder="Select level"
                ),

                # 🔽 Dropdown de Tipo
                html.Label("Type", className="mt-2"),
                dcc.Dropdown(
                    id="dropdown-tipo",
                    options=[
                        {"label": "NaN", "value": "value_nan"},
                        {"label": "Zero", "value": "value_zero"},
                        {"label": "Repeat", "value": "value_repeat"},
                    ],
                    placeholder="Select type"
                ),

            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-save-btn", className="me-2", color="secondary"),
                dbc.Button("Confirm", id="confirm-save-btn", className="btn btn-success"),
            ]),
        ], id="save-modal", is_open=False),

       
    ], className="p-4")
