from dash import html, dcc
import dash_bootstrap_components as dbc

def sidebar(session_data = None):
    is_admin = session_data and session_data.get("role") == "admin"
    is_authenticated = session_data and session_data.get("authenticated")

    return html.Div([
        dcc.Store(id="store-selected-state", storage_type="local"),
        dcc.Store(id='model-data-store', storage_type='local'),
        dcc.Store(id="previous-model", storage_type="local"),
        dcc.Store(id="store-prediction-control", data={"status": "stopped"}),
        # Stores the selection of Online or Offline data
        dcc.Store(id='store-selected-view', storage_type='local'),
        dcc.Store(id='store-selected-bucket', storage_type='local'),
        dcc.Store(id='store-selected-experiment', storage_type='local'),
        dcc.Store(id='store-metric-params', storage_type='memory'),
        # Stores which steps are enabled
        dcc.Store(id="step-store", data={"step": 1}),
        
        


        html.Hr(),
        html.Img(
            src="/assets/logo-white.png",
            className="logo-slider"
        ),
        html.P(
            "Soft sensor moniToring and mAintenance framework for Machine learning Models.", className="text-center"
        ),
        html.Hr() if is_authenticated else None,
        html.H4(f"Welcome, {session_data.get('user')}") if is_authenticated else None,
        dbc.Nav(
            [   
                dbc.NavLink(
                    html.Span([html.Span("1", className="circle-number"),html.Span("Data source", className="nav-text")], className="nav-item-content"),
                    href="/data-source",
                    className="sidebar-link",
                    active="exact",
                    id="step-1",
                ),
                # Main soft sensors link
                dbc.NavLink(
                    html.Span([html.Span("2", className="circle-number"),html.Span("Soft sensors", className="nav-text")], className="nav-item-content"),
                    href="/soft-sensors",
                    className="sidebar-link",
                    id="step-2",
                    active="exact"
                ),
                # Main monitoring
                dbc.NavLink(
                    html.Span([html.Span("3", className="circle-number"),html.Span("Monitoring", className="nav-text")], className="nav-item-content"),
                    href=None,
                    className="sidebar-link",
                    active="exact",
                    id="step-3",
                ),
                dbc.Collapse(
                    [
                        dbc.NavLink("Data Drift Detectors", href="/monitoring/data-drift", className="sidebar-link ms-4", id="data-drift-link"),
                        dbc.NavLink("Model divergence", href="/monitoring/performance", className="sidebar-link ms-4", id="performance-link"),
                    ], 
                    id="monitoring-collapse", 
                    is_open=False),
                dbc.NavLink(
                    html.Span([html.Span("4", className="circle-number"),html.Span("Simulation assessment", className="nav-text")], className="nav-item-content"),
                    href="/maintenance",
                    className="sidebar-link",
                    active="exact",
                    id="step-4",
                ),
                html.Hr(),
                dbc.NavLink("About us", href="/about-us", className="sidebar-link", active="exact"),
                dbc.NavLink("Help", href="/help", className="sidebar-link", active="exact"),
                # options administrator
                html.Hr() if is_admin else None,
                dbc.NavLink("Admin Panel", href="/admin", className="sidebar-link text-warning") if is_admin else None,
                dbc.NavLink([html.I(className="bi bi-box-arrow-right me-2"),"Logout"], id={"type": "logout-button", "index": 1}, className="sidebar-link text-danger") if is_authenticated else None,
            ],
            vertical=True,  # Ensures links are displayed one below the other
        )])
