from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

def create_input_section(model_options):
    return html.Div([
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
    ])

def create_data_table():
    return dash_table.DataTable(
        id='variable-table-maintenance',
        columns=[
            {"name": "Model", "id": "model"},
            {"name": "Variable Type", "id": "type"},
            {"name": "Variable Name", "id": "name"}
        ],
        data=[],
        editable=False,
        row_deletable=True,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "center"},
        style_header={"fontWeight": "bold", "backgroundColor": "lightgrey"}
    )

def get_maintenance_layout(model_options):
    return html.Div([
        html.H3("Maintenance Simulation", className="mb-4"),

        # Sección de entrada
        create_input_section(model_options),

        # Tabla
        html.Div([
            html.H5("Selected Variables"),
            create_data_table()
        ], className="mt-4"),

        # Gráfico
        dcc.Graph(id="maintenance-graph", className="mt-4"),
        dcc.Store(id="selected-variables-maintenance", data=[]),

        # Botones de acción
        dbc.Row([
            dbc.Col(dbc.Button("Save Simulation", id="save-simulations", color="success", className="w-100"), width=6),
            dbc.Col(dbc.Button("Set Maintenance", id="maintain-model", color="danger", className="w-100"), width=6)
        ], className="mt-4"),

        # Componente de descarga
        dcc.Download(id="download-excel"),

        # Modal: Guardar simulación
        dbc.Modal([
            dbc.ModalHeader("Confirm Save"),
            dbc.ModalBody("Do you want to save this simulation as an Excel file?"),
            dbc.ModalFooter([
                dbc.Button("Save", id="confirm-save", color="primary"),
                dbc.Button("Cancel", id="cancel-save", color="secondary")
            ])
        ], id="save-modal", is_open=False),

        # Modal: Justificación de mantenimiento
        dbc.Modal([
            dbc.ModalHeader("Set Maintenance"),
            dbc.ModalBody([
                dbc.Label("Reason for maintenance:"),
                dbc.Textarea(id="maintain-reason", placeholder="Write your reason here...", style={"width": "100%"})
            ]),
            dbc.ModalFooter([
                dbc.Button("Confirm", id="confirm-maintain", color="primary"),
                dbc.Button("Cancel", id="cancel-maintain", color="secondary")
            ])
        ], id="maintain-modal", is_open=False),
    ], className="p-4")
