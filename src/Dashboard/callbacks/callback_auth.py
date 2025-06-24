import dash
from dash import Input, Output, State, html, ALL
from Dashboard.layouts.auth_layout import login_form 
from Dashboard.layouts.main_layout import layout
from Dashboard.services.auth_service import authenticate

@dash.callback(
    Output("page-content", "children"),
    Output("user-session", "data"),
    Input("url", "pathname"),
    Input({"type": "logout-button", "index": ALL}, "n_clicks"),
    State("user-session", "data"),
    prevent_initial_call="initial_duplicate"
)
def display_main_page(pathname, logout_clicks, session_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Detecta logout por ID dinámico solo si se hizo clic
    if trigger_id.startswith("{") and logout_clicks:
        import json
        trigger_id_dict = json.loads(trigger_id)
        
        if trigger_id_dict.get("type") == "logout-button":
            
            # Recorremos clicks y ejecutamos logout solo si alguno fue clickeado
            for clicks in logout_clicks:
                if clicks and clicks > 0:
                    print(">> Logout ejecutado")
                    return login_form(), {}

    # Si no está autenticado
    if not session_data or not session_data.get("authenticated"):
        return login_form(), session_data

    # Navegación normal, permanece en layout principal
    return layout(session_data), session_data

@dash.callback(
    Output("user-session", "data",allow_duplicate=True),
    Output("page-content", "children",allow_duplicate=True),
    Output("login-message", "children"),
    Input("login-button", "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True
)
def handle_login(n_clicks, username, password):
    if not username or not password:
        return {}, login_form(), "Username or password none"

    username = username.strip()
    password = password.strip()
    user = authenticate(username, password)

    if user:
        session_data = {"authenticated": True, "user": user["username"], "role": user["role"]}
        return session_data, layout(session_data), ""
    
    return {}, login_form(), "Username o password incorrects"


@dash.callback(
    Output("login-password", "type"),
    Output("toggle-password", "children"),
    Input("toggle-password", "n_clicks"),
    State("login-password", "type"),
)
def toggle_password_visibility(n_clicks, current_type):
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    # Toggle password visibility
    new_type = "text" if current_type == "password" else "password"
    new_icon = html.I(className="bi bi-eye-slash-fill") if new_type == "text" else html.I(className="bi bi-eye-fill")

    return new_type, new_icon
