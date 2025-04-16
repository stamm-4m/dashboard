import logging

from dash import html, dcc
import dash_bootstrap_components as dbc  # type: ignore


def sidebar():
    logging.info("Creating sidebar")
    return html.Div([
        html.H2("STAMM", className="fw-bold text-center"),
        dcc.Store(id="store-selected-state", storage_type="local"),
        dcc.Store(id='model-data-store', storage_type='local'),
        # Almacena la seleccion Online o Offline data
        dcc.Store(id='store-selected-view', storage_type='local'),
        dcc.Store(id='store-selected-bucket', storage_type='local'),
        dcc.Store(id='store-selected-experiment', storage_type='local'),
        # Almacena qué pasos están habilitados
        dcc.Store(id="step-store", data={"step": 1}),

        
        html.Hr(),
        html.P(
            "Soft sensor moniToring and mAintenance framework for Machine learning Models.", className="text-center"
        ),
        dbc.Nav(
            [   
                dbc.NavLink(
                    html.Span([html.Span("1", className="circle-number"),html.Span("Data source", className="nav-text")], className="nav-item-content"),
                    href="/data-source",
                    className="sidebar-link",
                    active="exact",
                    id="step-1",
                ),
                # Link main sof sensors
                dbc.NavLink(
                    html.Span([html.Span("2", className="circle-number"),html.Span("Soft sensors", className="nav-text")], className="nav-item-content"),
                    href="#",
                    className="sidebar-link",
                    id="step-2",
                    active="exact"
                ),
                # Secciones colapsables (Offline y Online)
                dbc.Collapse(
                    [
                        dbc.NavLink(
                            "Offline",
                            href="/soft-sensors/offline",
                            className="sidebar-link ms-4",  # Margen para subnivel
                            disabled=True,  # Valor predeterminado deshabilitado
                            id="offline-link",
                        ),
                        dbc.NavLink(
                            "Online",
                            href="/soft-sensors/online",
                            className="sidebar-link ms-4",  # Margen para subnivel
                            disabled=True,  # Valor predeterminado deshabilitado
                            id="online-link",
                        ),
                        dbc.NavLink("Load soft sensor", href="/soft-sensors/load-soft-sensor", className="sidebar-link ms-4", id="load-soft-link"),
                    ],
                    id="soft-sensors-collapse",
                    is_open=False,  # Empieza cerrado
                ),
                # main monitoring
                dbc.NavLink(
                    html.Span([html.Span("3", className="circle-number"),html.Span("Monitoring", className="nav-text")], className="nav-item-content"),
                    href="#",
                    className="sidebar-link",
                    active="exact",
                    id="step-3",
                ),
                dbc.Collapse(
                    [
                        dbc.NavLink("Data Drift Detectors", href="/monitoring/data-drift", className="sidebar-link ms-4", id="data-drift-link"),
                        dbc.NavLink("Performance Estimators", href="/monitoring/performance", className="sidebar-link ms-4", id="performance-link"),
                    ], 
                    id="monitoring-collapse", 
                    is_open=False),
                dbc.NavLink(
                    html.Span([html.Span("4", className="circle-number"),html.Span("Maintenace", className="nav-text")], className="nav-item-content"),
                    href="/maintenace",
                    className="sidebar-link",
                    active="exact",
                    id="step-4",
                ),
                html.Hr(),
                dbc.NavLink("About us", href="/about-us", className="sidebar-link", active="exact"),
                dbc.NavLink("Help", href="/help", className="sidebar-link", active="exact")
            ],
            vertical=True,  # Hace que los enlaces estén uno debajo del otro
            #pills=True      # Agrega un efecto de resaltado en el enlace activo
        )])
