from dash import html, dcc
import dash_bootstrap_components as dbc

def login_form():
    return html.Div(
        [
            dcc.Location(id="url-login", refresh=True),

            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        # Logo at the top
                        html.Div(
                            html.Img(src="/assets/logo.png", style={
                                "maxWidth": "160px", "marginBottom": "25px"
                            }),
                            className="text-center"
                        ),

                        dbc.Card([
                            dbc.CardHeader(html.H4("Sign In", className="text-center")),

                            dbc.CardBody([
                                # Username input with icon
                                html.Div([
                                    dbc.Label("Username", html_for="username"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="bi bi-person-fill")),
                                        dbc.Input(
                                            id="login-username",
                                            placeholder="Enter your username",
                                            type="text"
                                        )
                                    ])
                                ], className="mb-3"),

                                # Password input with icon
                                html.Div([
                                    dbc.Label("Password", html_for="password"),
                                    dbc.InputGroup([
                                        dbc.InputGroupText(html.I(className="bi bi-lock-fill")),
                                        dbc.Input(
                                            id="login-password",
                                            placeholder="Enter your password",
                                            type="password"
                                        ),
                                         dbc.Button(
                                            html.I(className="bi bi-eye-fill"),
                                            id="toggle-password",
                                            color="light",
                                            n_clicks=0,
                                            className="border"
                                        )
                                    ])
                                ], className="mb-3"),

                                # Remember me checkbox and Register link
                                html.Div([
                                    dbc.Checkbox(id="remember-me", className="me-2"),
                                    dbc.Label("Remember me", html_for="remember-me", className="me-auto"),
                                    html.A("Register", href="/register", className="ms-auto text-primary"),
                                ], className="d-flex justify-content-between align-items-center mb-3"),

                                # Login button
                                dbc.Button("Sign In", id="login-button", color="primary", className="w-100"),

                                # Message output
                                html.Div(id="login-message", className="text-danger mt-3", style={"minHeight": "2em"})
                            ])
                        ], className="shadow p-4", style={"borderRadius": "1rem"})
                    ], width=12, md=6, lg=4)
                ], justify="center", align="center", className="vh-100")
            ])
        ]
    )
