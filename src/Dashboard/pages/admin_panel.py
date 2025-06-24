from dash import html, dcc
import dash_bootstrap_components as dbc

def admin_panel_layout(username="Admin"):
    return html.Div(
        [
            dcc.Location(id="url-admin", refresh=True),

            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H2([
                            html.I(className="bi bi-speedometer2 me-2"),
                            "Admin Panel"
                        ], className="text-center mb-4"),
                    ], width=12)
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="bi bi-people-fill me-2 fs-3"),
                                    html.H4("User Management", className="mt-2"),
                                    html.P("Manage system users and roles.", className="text-muted")
                                ], className="text-center"),

                                dbc.Button("Go", id="admin-users", color="primary", className="mt-3 w-100")
                            ])
                        ], className="shadow h-100")
                    ], width=12, md=4, lg=4),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="bi bi-bar-chart-fill me-2 fs-3"),
                                    html.H4("Reports", className="mt-2"),
                                    html.P("View system analytics and reports.", className="text-muted")
                                ], className="text-center"),

                                dbc.Button("Go", id="admin-reports", color="info", className="mt-3 w-100")
                            ])
                        ], className="shadow h-100")
                    ], width=12, md=4, lg=4),

                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="bi bi-gear-fill me-2 fs-3"),
                                    html.H4("Settings", className="mt-2"),
                                    html.P("Adjust system configurations.", className="text-muted")
                                ], className="text-center"),

                                dbc.Button("Go", id="admin-settings", color="secondary", className="mt-3 w-100")
                            ])
                        ], className="shadow h-100")
                    ], width=12, md=4, lg=4),
                ], className="justify-content-center mt-4")
            ], fluid=True)
        ]
    )
