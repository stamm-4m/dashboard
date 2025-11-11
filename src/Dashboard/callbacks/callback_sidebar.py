import dash
from dash import Input, Output, State
from Dashboard.layouts.auth_layout import login_form 
from Dashboard.pages.data_source import data_source_layout
from Dashboard.pages.softsensors import softsensors_layout
from Dashboard.pages.data_drift import data_drift_layout
from Dashboard.pages.model_upload import model_upload_layout
from Dashboard.pages.performance_estimator import performance_estimator_layout
from Dashboard.pages.help import help_layout
from Dashboard.pages.about_us import about_us_layout
from Dashboard.pages.not_found import not_found_layout
from Dashboard.pages.home import home_layout
from Dashboard.pages.maintenance import maintenance_layout
from Dashboard.pages.admin_panel import admin_panel_layout

# Callback to handle sections
@dash.callback(
    Output("main-content", "children"),
    Input("url", "pathname"),
    State("user-session", "data"))
def display_page(pathname, session_data):
    if not session_data or not session_data.get("authenticated"):
        return login_form()
    if pathname == "/" or pathname == "/home":
        return home_layout()
    if pathname == "/data-source":
        return data_source_layout()
    elif pathname == "/soft-sensors":
        return softsensors_layout()
    elif pathname == "/soft-sensors/load-soft-sensor":
         return model_upload_layout()
    elif pathname == "/monitoring/data-drift":
        return data_drift_layout()
    elif pathname == "/monitoring/performance":
         return performance_estimator_layout()
    elif pathname == "/maintenance":
         return maintenance_layout()
    elif pathname == "/about-us":
         return about_us_layout()
    elif pathname == "/help":
        return help_layout()
    if pathname == "/admin":
        return admin_panel_layout()
    else:
        return not_found_layout()
    

@dash.callback(
    Output("monitoring-collapse", "is_open"), 
    Input("step-3", "n_clicks"), 
    prevent_initial_call=True
)
def toggle_monitoring(n):
    return True if n and n % 2 != 0 else False

@dash.callback(
    [
        Output("data-drift-link", "className"), 
        Output("performance-link", "className"),
    ], 
    Input("url", "pathname"),
)
def update_monitoring_links(pathname):
    data_drift_class = "sidebar-link ms-4 active" if pathname == "/monitoring/data-drift" else "sidebar-link ms-4"
    performance_class = "sidebar-link ms-4 active" if pathname == "/monitoring/performance" else "sidebar-link ms-4"
    return data_drift_class, performance_class

step_data = {"step": 1}
# 📌 Callback to update state when the page changes
@dash.callback(
    Output("step-store", "data"),
    Input("url", "pathname"),  # Detects changes in the URL
    State("step-store", "data"),
)
def update_step(pathname, step_data):
    step = step_data["step"]

    # Define steps and their URLs
    step_paths = {
        "/data-source": 1,
        "/soft-sensors": 2,
        "/monitoring/data-drift": 3,
        "/monitoring/performance": 3,
        "/maintenance": 4
    }

    # If the URL belongs to a step and is greater than the current one, update the state
    if pathname in step_paths and step_paths[pathname] >= step:
        return {"step": step_paths[pathname] + 1}

    return step_data  # No change if already advanced


# 📌 Callback to enable/disable steps based on stored state
@dash.callback(
    Output("step-2", "disabled"),
    Output("step-3", "disabled"),
    Output("step-4", "disabled"),
    Input("step-store", "data")
)
def enable_next_steps(step_data):
    step = step_data["step"]
    return step < 2, step < 3, step < 4  # Enables progressively