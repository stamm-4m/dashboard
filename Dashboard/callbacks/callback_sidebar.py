import dash
from dash import Input, Output, html, State
from pages.data_source import data_source_layout
from pages.softsensor_offline import sofsensor_offline_layout
from pages.softsensor_online import softsensor_online_layout
from pages.data_drift import data_drift_layout
from pages.model_upload import model_upload_layout
from pages.performance_estimator import performance_estimator_layout
from pages.help import help_layout
from pages.about_us import about_us_layout
from pages.not_found import not_found_layout
from pages.home import home_layout
from pages.maintenance import maintenance_layout

# Callback to handle sections
@dash.callback(
    Output("page-content", "children"),
    Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/" or pathname == "/home":
        return home_layout()
    if pathname == "/data-source":
        return data_source_layout()
    elif pathname == "/soft-sensors/offline":
        return sofsensor_offline_layout()
    elif pathname == "/soft-sensors/online":
        return softsensor_online_layout()
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
    else:
        return not_found_layout()
    

# Callback to toggle soft sensors Offline/Online option
@dash.callback(
    Output("soft-sensors-collapse", "is_open"),
    Input("step-2", "n_clicks"),
    prevent_initial_call=True
)
def toggle_soft_sensors(n):
    return True if n and n % 2 != 0 else False 

@dash.callback(
    Output("monitoring-collapse", "is_open"), 
    Input("step-3", "n_clicks"), 
    prevent_initial_call=True
)
def toggle_monitoring(n):
    return True if n and n % 2 != 0 else False

@dash.callback(
    [
        Output("offline-link", "className"),
        Output("online-link", "className"),
    ],
    Input("url", "pathname"),
)
def update_active_links(pathname):
    # Add "active" class only if the URL matches
    offline_class = "sidebar-link ms-4 active" if pathname == "/soft-sensors/offline" else "sidebar-link ms-4"
    online_class = "sidebar-link ms-4 active" if pathname == "/soft-sensors/online" else "sidebar-link ms-4"
    return offline_class, online_class

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
        "/soft-sensors/offline": 2,
        "/soft-sensors/online": 2,
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