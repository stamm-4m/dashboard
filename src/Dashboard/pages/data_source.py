from dash import html,dcc, dash_table
import dash_bootstrap_components as dbc
from datetime import date, timedelta
from Dashboard.InfluxDb import influxdb_handler
from Dashboard.utils.utils_global import disabled_figure
import logging
logger = logging.getLogger(__name__)

def data_source_layout(store_data=None):
        
        
        example_data = [
            {"Type": "Sensor", "Name": "Temperature", "Unit": "°C", "Mean": "30", "Max": "40", "Min": "20"},
            {"Type": "Actuator", "Name": "substrate_concentration", "Unit": "g/L", "Mean": "15", "Max": "25", "Min": "10"},
            {"Type": "Computed variable", "Name": "vessel_volume", "Unit": "L", "Mean": "1000", "Max": "1200", "Min": "800"},
        ]

        experiment_columns = [
            {"name": "Experiment ID", "id": "Experiment ID"},
            {"name": "Start Time", "id": "Start Time"},
            {"name": "End Time", "id": "End Time"},
            {"name": "Batch size", "id": "Batch size"}
        ]

        time_units = ["seconds", "minutes", "hours", "days", "months"]

        selected_project = None
        selected_experiment = None
        logger.debug(f"Received store data in layout: {store_data}")
        if store_data:
            selected_project = store_data.get("selected_project")
            selected_experiment = store_data.get("selected_experiment")

        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H5("Data source", className="fw-bold d-inline")
                    ], className="d-flex align-items-left"),
                    dcc.Interval(
                        id='interval-component',
                        interval=5 * 1000,  # 5 segundos
                        n_intervals=0
                    ),
                    dbc.Label("Please choose an Project to load available experiments:", className="fw-bold"),
                    dcc.Dropdown(
                        id="project-dropdown",
                        placeholder="Project Data Browser",
                        className="mb-3",
                        value=selected_project,
                        options=[],
                        persistence=True,
                        persistence_type="local"
                    ),
                    dbc.Label("Please choose an Experiment ID to load the available models:", className="fw-bold"),
                    dcc.Dropdown(
                        id="experiment-dropdown",
                        placeholder="Experiment Data Browser",
                        className="mb-3",
                        value=selected_experiment,
                        options=[],
                        persistence=True,
                        persistence_type="local"
                    ),
                    # Row for model details
                    html.H5(id="project-name", className="fw-bold"),

                    dbc.Label("Project description:", className="fw-bold"),
                    dbc.Row(
                        
                        html.Div(id='project-details')
                        
                    ),

                    #Summary report
                    html.H5("Statistical summary", className="text-left mt-4"),
                    html.Div("Duration: N/A", id="duration-text", className="fw-bold text-primary fs-5 mb-3"),
                    html.Div(id="table-title-container",style={"textAlign": "center", "marginTop": "10px"}),
                    dash_table.DataTable(
                        id="data-table",
                        columns=[
                            {"name": "Type", "id": "Type"},
                            {"name": "Name", "id": "Name"},
                            {"name": "Unit", "id": "Unit"},
                            {"name": "Mean", "id": "Mean"},
                            {"name": "Max", "id": "Max"},
                            {"name": "Min", "id": "Min"}
                        ],
                        data=example_data,
                        page_size=10,
                    ),

                    html.H5("Time Unit for 'Recent Measurements'", className="text-left mt-4"),
                    html.Div([
                    # Tabla Experimentos Online
                    dbc.Input(
                        id='time-value-selector',
                        type='number',
                        min=1,
                        value=5,
                    ),
                    dcc.Dropdown(
                        id='time-unit-selector',
                        options=[{"label": unit.capitalize(), "value": unit} for unit in time_units],
                        value="minutes",
                        clearable=False,
                    ),
                    ], style={
                        
                    }),
                    dbc.Alert(id="experiment-message", is_open=False, duration=8000),
                    html.Div([
                        dash_table.DataTable(
                            id="table-experiments-online",
                            columns=experiment_columns,
                            data=[],
                            page_size=5,
                            style_table={"overflowX": "auto"},
                        )
                    ], className="mb-4"),

                    # Data by experiment
                    html.H5("Data Point Distribution"),
                    dbc.Label("Range selection"),
                    html.Br(),
                    dcc.DatePickerRange(
                        id='ds-date-picker-range',
                        min_date_allowed=date(1995, 8, 5),
                        max_date_allowed=date.today() + timedelta(days=1),
                        initial_visible_month=date.today(),
                        start_date=date.today().replace(day=1),
                        end_date=date.today()   
                    ),
                    html.Div(id='output-container-date-picker-range'),
                    dbc.Label("Field(s) to count"),
                    dcc.Dropdown(
                        id="field-selector",
                        options=[],
                        value="all",
                        clearable=False
                    ),
                    dcc.Graph(id='line-experiments', figure=disabled_figure),


                ], width=12, className="p-3 bg-light rounded-3 shadow-sm"),
            ], className="my-4"),

            dbc.Row([
                
            ], className="my-4"),
        ], fluid=True)