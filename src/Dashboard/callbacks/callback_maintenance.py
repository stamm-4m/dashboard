import os
from dash import Input, Output, State, dcc, ALL, ctx, html,no_update
from dash import callback_context

import dash_bootstrap_components as dbc
import dash
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from Dashboard.InfluxDb import influxdb_handler # retrieve the created instance
import io
import sqlite3
from Dashboard.utils import model_information,sqlite_handler
import plotly.express as px
from Dashboard.utils.utils_maintenance import generate_prediction_name
from Dashboard.config import INFLUXDB, BASE_URL_API, INFLUXDB_BUCKET


dfc = pd.DataFrame()
#set model pre selected 
@dash.callback(
            Output("model-selector-maintenance", "value"),
            Input("model-data-store", "data")
)
def update_model_display(data):
            if not data or "model_name" not in data or not data["model_name"]:
                model_options = model_information.get_model_name_options()
                return "No selected model"
            return f"{data['model_name']}"
# show experiment ID selected
@dash.callback(
            Output("experiment-id-display-maintenence", "children"),
            Input("store-selected-state", "data"),
)
def update_experiment_display(data):
            if not data or "selected_experiment" not in data or not data["selected_experiment"]:
                return "No experiment ID Selected"
            return f"{data['selected_experiment']}"
 

# Confirm maintenance
@dash.callback(
        Output("maintain-reason", "value"),
        Input("confirm-maintain", "n_clicks"),
        State("maintain-reason", "value"),
        prevent_initial_call=True
    )
def confirm_maintenance(n_clicks, reason):
        if reason:
            print(f"Maintenance confirmed with reason: {reason}")
            return ""
        return dash.no_update

# Function to update the ypes  of model inputs
@dash.callback(
            Output('type-selector-maintenance', 'options'),
            Input('model-selector-maintenance', 'value'),
            prevent_initial_call=True
        )
def update_model_types_maintenance(name):
            types_variable = model_information.get_unique_types_models(name)
            if types_variable is None:
                  print("types_variable",types_variable)
                  return []
            return types_variable
@dash.callback(
            Output('name-selector-maintenance', 'options'),
            Input('type-selector-maintenance', 'value'),
            Input('model-selector-maintenance', 'value')
        )
def update_name_selector(selected_category,model_name):
            """
            Update the options for the 'name-selector-maintenance' dropdown based on the selected category.

            Args:
                selected_category (str): The category selected in the 'type-selector-maintenance' dropdown.

            Returns:
                list: A list of dictionaries with the options for the 'name-selector-maintenance' dropdown.
            """
            if selected_category:
                # Get names corresponding to the selected category
                print("name_variable: ",model_information.get_names_by_category(selected_category,model_name))
                return model_information.get_names_by_category(selected_category,model_name)
            else:
                # Return an empty list if no category is selected
                return []
            
# Callback to update the maintenance graph
@dash.callback(
    Output("maintenance-graph", "figure"),
    Output("prediction-table", "data"),  
    Output("prediction-table", "columns"),
    Input("model-data-store", "data"),
    Input("store-selected-state", "data"),
    Input("time-window-slider", "value"),
    Input("add-variable-btn-maintenance", "n_clicks"),
    Input("selected-variables-maintenance", "data"),
    State("maintenance-graph", "figure"),
    prevent_initial_call=True
)
def update_graph_var_maintenance(data,data_exp,range_slider, n_clicks, selected_variables, current_figure):
    global dfc
    if not data_exp or "selected_experiment" not in data_exp or not data_exp["selected_experiment"]:
        print("No experiment ID Selected")
        return go.Figure(), [],[]
    
    dfc = influxdb_handler.get_data_by_batch_id2(data_exp["selected_experiment"])
    print("dfc: ",dfc)
    dfc["_time"] = pd.to_datetime(dfc["_time"], errors="coerce")

    timestamps = sorted(dfc["_time"].dropna().unique())
    start_time = timestamps[range_slider[0]]
    end_time = timestamps[range_slider[1]]
    dfc = dfc[(dfc["_time"] >= start_time) & (dfc["_time"] <= end_time)]
    
    if not data or "model_name" not in data or not data["model_name"]:
        print("no data model name")
        return go.Figure(),[],[]
    
    prediction_var = generate_prediction_name(data["model_name"])
    #data for table section
    # Columnas base
    columns_to_show = ["_time", prediction_var]

    # Agregar variables seleccionadas
    if selected_variables:
        for var_data in selected_variables:
            if isinstance(var_data, dict) and "variable_name" in var_data:
                var = var_data["variable_name"]
                if var in dfc.columns and var not in columns_to_show:
                    columns_to_show.append(var)

    # Filtrar el DataFrame
    table_df = dfc[columns_to_show].dropna(subset=[prediction_var])

    # Guardar columnas originales sin formato
    table_df["raw_time"] = table_df["_time"]
    if prediction_var in table_df.columns:
        table_df["raw_prediction"] = table_df[prediction_var]

    # Formato fecha y predicción
    table_df["time_str"] = table_df["_time"].dt.strftime('%m/%d/%Y %H:%M:%S.%f')
    if prediction_var in table_df.columns:
        table_df[prediction_var+"_str"] = table_df[prediction_var].round(4)

    # Agregar columna "Reportar"
    table_df["Report"] = [
        f"[🚨 Report](#report-{i})" for i in range(len(table_df))
    ]
    
    # Para mostrar en la tabla: eliminamos _time original y renombramos time_str a _time
    table_for_dash = table_df.drop(columns=["_time"]).rename(columns={"time_str": "_time"})
    table_for_dash = table_for_dash.drop(columns=[prediction_var]).rename(columns={prediction_var+"_str": prediction_var})

    # Preparar tabla con markdown
    table_data = table_for_dash.to_dict("records")
    # Columnas visibles
    table_columns = [
        {"name": col, "id": col} for col in table_for_dash.columns if col not in ["Report", "raw_time", "raw_prediction"]
    ]
    table_columns.append({
        "name": "Anomaly",
        "id": "Report",
        "presentation": "markdown"
    })
    hidden_columns = ["raw_time", "raw_prediction"]


    print(f"🔄 Callback executed - Clicks: {n_clicks}, Selected variables: {selected_variables}")

    if not selected_variables:
        print("⚠ No variables selected.")

    if dfc is None or "_time" not in dfc:
        print("⚠ No data or missing '_time' column.")
        return go.Figure(current_figure) if current_figure else go.Figure(),[],[]

    df = pd.DataFrame(dfc)
    df["_time"] = pd.to_datetime(df["_time"], errors="coerce")

    fig = go.Figure()

    colors = px.colors.qualitative.Dark24
    existing_traces = set()

    # --- Línea principal: CART_penicillin_prediction en eje Y principal ---
    if prediction_var in df.columns:
        fig.add_trace(go.Scatter(
            x=df["_time"].astype(str),
            y=df[prediction_var],
            mode="lines",
            name=prediction_var,
            yaxis="y",
            line=dict(color="black", dash="dash")
        ))
        existing_traces.add(prediction_var)
        print(f"✅ Línea '{prediction_var}' agregada al eje principal.")
    else:
        print(f"⚠ '{prediction_var}' no existe en los datos.")

    # --- Agregar variables seleccionadas ---
    for i, var_data in enumerate(selected_variables):
        if not isinstance(var_data, dict) or "variable_name" not in var_data:
            print(f"⚠ Formato inválido en selected_variables[{i}]: {var_data}")
            continue

        var = var_data["variable_name"]

        if var in df.columns and var not in existing_traces:
            color = colors[i % len(colors)]
            axis_id = f"y{i + 3}"  # y3, y4, etc. (y y2 ya está usado)

            fig.add_trace(go.Scatter(
                x=df["_time"].astype(str),
                y=df[var],
                mode="lines",
                name=var,
                yaxis=axis_id,
                line=dict(color=color)
            ))
            existing_traces.add(var)
            print(f"✅ Variable '{var}' agregada al gráfico en eje {axis_id}.")
        else:
            print(f"⚠ '{var}' ya está graficada o no existe.")

    # Ejes adicionales para cada variable seleccionada
    extra_axes = {}
    for i, var_data in enumerate(selected_variables):
        axis_name = f"yaxis{i + 3}"  # yaxis3, yaxis4, ...
        side = "right"
        position = 1.0 - (i * 0.10) 

        extra_axes[axis_name] = dict(
            title=dict(
                text=var_data["variable_name"],
                font=dict(color=colors[i % len(colors)])
            ),
            tickfont=dict(color=colors[i % len(colors)]),
            anchor="x",
            overlaying="y",
            side=side,
            position=position,
            showgrid=False
        )

    fig.update_layout(
        xaxis=dict(title="Time", tickangle=-45, type="date"),
        yaxis=dict(
            showgrid=True,
            title=dict(
                text=prediction_var,
                font=dict(color="black")
            )
        ),
        yaxis2=dict(
            visible=False  # ya no se usará y2
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        **extra_axes
    )

    print(f"📊 Gráfico finalizado con {len(fig.data)} trazas.")
    return fig, table_data, table_columns

@dash.callback(
    Output("time-slider-labels", "children"),
    Output("time-window-slider", "max"),
    Input("store-selected-state", "data"),
    Input("time-window-slider", "value"),
    State("maintenance-graph", "figure")
)
def update_slider_labels(data,slider_range, figure):
    if not data or "selected_experiment" not in data or not data["selected_experiment"]:
        print("No experiment ID Selected")
        return "", 0

    dfc = influxdb_handler.get_data_by_batch_id2(data['selected_experiment'])
    start_idx, end_idx = slider_range
    if not dfc.empty:
        timestamps = sorted(dfc["_time"].dropna().unique())
        start_time = timestamps[start_idx] if start_idx < len(timestamps) else timestamps[0]
        end_time = timestamps[end_idx] if end_idx < len(timestamps) else timestamps[-1]

        start_str = pd.to_datetime(start_time).strftime('%Y-%m-%d %H:%M:%S')
        end_str = pd.to_datetime(end_time).strftime('%Y-%m-%d %H:%M:%S')

        return f"From: {start_str}  ➡  To: {end_str}", len(timestamps)
    return "", 0


@dash.callback(
            Output("selected-variables-maintenance", "data", allow_duplicate=True),
            Output("variable-table-maintenance", "children"),
            Input("add-variable-btn-maintenance", "n_clicks"),
            Input({"type": "remove-btn", "index": ALL}, "n_clicks"),
            [State('name-selector-maintenance', 'value'),
            State("selected-variables-maintenance", "data")],
            prevent_initial_call=True
        )
def update_table(add_click, remove_clicks, selected_variable, current_data):
            if current_data is None:
                current_data = []

            # Check if Add button is clicked
            if ctx.triggered_id == "add-variable-btn-maintenance" and add_click:
                #Validate that the variable is not already in the list
                if selected_variable and selected_variable not in [v["variable_name"] for v in current_data]:
                    current_data.append({"variable_name": selected_variable})

            # Check if Remove button is clicked
            elif isinstance(ctx.triggered_id, dict) and ctx.triggered_id["type"] == "remove-btn":
                index_to_remove = ctx.triggered_id["index"]
                if 0 <= index_to_remove < len(current_data):
                    current_data.pop(index_to_remove)

            # Generate the table rows dynamically
            rows = [
                html.Tr([
                    html.Td(variable["variable_name"], className="text-center"),
                    html.Td(
                        dbc.Button(
                            "Remove",
                            id={"type": "remove-btn", "index": int(i)},
                            color="danger",
                            size="sm",
                            className="remove-btn text-center"
                        )
                    )
                ]) for i, variable in enumerate(current_data)
            ]
            # Add table header
            table_header = html.Tr([html.Th("Variable monitoring", className="text-center"), html.Th("Action", className="text-center")])
            table_body = [table_header] + rows

            # Wrap table with compact class
            table = dbc.Table(table_body, bordered=True, hover=True, striped=True, className="table-sm text-center")
            print("current_data:",current_data)
            print("table:",table)
            return current_data, table

@dash.callback(
    Output("save-confirmation", "children"),
    Input("store-selected-state", "data"),
    Input("model-data-store", "data"),
    Input("confirm-save-btn", "n_clicks"),
    State("prediction-table", "data"),
    State("clicked-report-info", "data"),
    State("dropdown-nivel", "value"),
    State("dropdown-tipo", "value"),
    prevent_initial_call=True
)
def save_selected_row_to_influx(data_exp, data, n_clicks, table_data, row_data, nivel, tipo):
    # Check if a row is selected
    #if not table_data or row_index is None or row_index >= len(table_data):
    #    return "⚠ Please select a row by clicking on it."

    prediction_var = generate_prediction_name(data["model_file"])
    row = row_data
    print(prediction_var)
    # Ensure the required fields are present
    if "raw_time" not in row:
        return "❌ The selected row does not contain the required fields."

    try:
        # to save point Local file
        value = row["raw_prediction"]
        if value is None or value == "":
            return "⚠ The prediction value is empty."

        # New point with the same data but with additional tags
        point = {
            "measurement": str(data_exp["selected_experiment"]),
            "tags": {
                "level": str(nivel),
                "type": str(tipo),
            },
            "time": row["raw_time"],
            "fields": {
                prediction_var: float(value)
            }
        }
        # NO update influx data
        #influxdb_handler.update_point_tags_safe(data_exp["selected_experiment"],row["raw_time"],prediction_var,float(value),{"type": str(tipo), "level": str(nivel)})
        sqlite_handler.upsert_point(
            data_exp["selected_experiment"],
            row["raw_time"],
            prediction_var,
            float(value),
            {"type": str(tipo), "level": str(nivel)}
        )
        return "✅ Point saved with tags in SQLite."
    except Exception as e:
        return f"❌ Error saving the point to InfluxDB: {e}"
    
@dash.callback(
    Output("anomaly-warning", "style"),
    Input("prediction-table", "data")
)
def toggle_anomaly_warning(table_data):
    if table_data and len(table_data) > 0:
        return {"display": "block"}
    return {"display": "none"}

@dash.callback(
    Output("save-modal", "is_open", allow_duplicate=True),
    Input("confirm-save-btn", "n_clicks"),
    Input("cancel-save-btn", "n_clicks"),
    State("clicked-report-info", "data"),
    prevent_initial_call=True
)
def process_report(confirm_clicks, cancel_clicks, report_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "cancel-save-btn":
        return False  # Close the modal without doing anything

    if trigger_id == "confirm-save-btn":
        # Here you could save the anomaly to a database or log
        print(f"✅ Anomaly reported at: {report_data}")
        # TODO: save or send the data
        return False  # Close the modal

    return dash.no_update

@dash.callback(
    Output("save-modal", "is_open"),
    Output("clicked-report-info", "data"),
    Input("prediction-table", "active_cell"),
    State("prediction-table", "data"),
    prevent_initial_call=True
)
def handle_report_click(active_cell, table_data):
    if active_cell and active_cell.get("column_id") == "Report":
        row_idx = active_cell["row"]
        row_data = table_data[row_idx]
        print("row_data",row_data)
        return True, row_data  # open modal with data

    return False, dash.no_update

@dash.callback(
    Output("download-excel-report", "data"),
    Input("generate-report-btn", "n_clicks"),
    Input("model-data-store", "data"),
    State("experiment-id-display-maintenence", "children"),
    State("model-selector-maintenance", "value"),
    State("time-window-slider", "value"),
    State("selected-variables-maintenance", "data"),
    State("prediction-table", "data"),
    prevent_initial_call=True
)
# Generate Report
def generate_excel_report(n_clicks,data, experiment_id, model_selected, time_range, selected_vars, table_data):
    # Sheet1: Info general
    #get name var prediction
    prediction_var = generate_prediction_name(data["model_file"])

    info_dict = {
        "Experiment ID": [experiment_id],
        "User": [experiment_id],
        "Selected model": [model_selected],
        "Time range start": [time_range[0]],
        "Time range end": [time_range[1]],
        "Selected variables": [", ".join([f"{v['variable_name']}" for v in selected_vars])],
        "Model metadata": [f"{BASE_URL_API}/metadata/{prediction_var.split('_')[-1]}"],
        "Database": [INFLUXDB], 
        "Bucket": [INFLUXDB_BUCKET], 
    }
    df_info = pd.DataFrame(info_dict)

    # Sheet2: Prediction Table
    df_prediction = pd.DataFrame(table_data)
    selected_columns = [v['variable_name'] for v in selected_vars]

    columns_dict = {
        "Timestamp": df_prediction["raw_time"],
        "Simulation": df_prediction["raw_prediction"]
    }

    for var in selected_columns:
        if var in df_prediction.columns:
            columns_dict[var] = df_prediction[var]

    df_transformed_pred = pd.DataFrame(columns_dict)

    # Sheet3: Data from SQLite (point_report)
    try:
        # Obtiene el path absoluto relativo a este archivo Python
        base_path = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_path, "..", "Data", "point_report.db")
        conn = sqlite3.connect(db_path)
        df_report = pd.read_sql_query(
            "SELECT * FROM point_report WHERE measurement = ?", 
            conn, 
            params=(experiment_id,)
        )
        conn.close()
        #data printeable for excel
        df_transformed_report = pd.DataFrame({
            "timestamp": df_report["time"],
            "_measurement": "Experiment ID",  # valor fijo
            "measurement_value": df_report["measurement"],
            "tag_1": df_report["type"],
            "tag_2": df_report["level"],
            "field_1": df_report["prediction_var"],
            "field_value": df_report["value"]
        })
    except Exception as e:
        df_report = pd.DataFrame({"error": [str(e)]})
        df_transformed_report = pd.DataFrame({"error": [str(e)]})

    # Adjust simulation data add type and level
    if not df_transformed_pred.empty and not df_report.empty:

        # 1. Convertir ambas columnas a datetime
        df_transformed_pred["Timestamp"] = pd.to_datetime(df_transformed_pred["Timestamp"], format="ISO8601")
        df_report["time"] = pd.to_datetime(df_report["time"], format="ISO8601")

        # 2. Hacer el merge por timestamp
        df_transformed_pred = pd.merge(
            df_transformed_pred,
            df_report[["time", "type", "level"]],
            left_on="Timestamp",
            right_on="time",
            how="left"
        )

        # 3. Eliminar la columna duplicada 'time' (opcional)
        df_transformed_pred.drop(columns=["time"], inplace=True)
        # Eliminar zona horaria de las columnas datetime
        df_transformed_pred["Timestamp"] = df_transformed_pred["Timestamp"].astype(str)
    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_info.to_excel(writer, index=False, sheet_name="Metadata")
        df_transformed_pred.to_excel(writer, index=False, sheet_name="Simulation")
        df_transformed_report.to_excel(writer, index=False, sheet_name="Flagged Measurements_DB")
    output.seek(0)

    return dcc.send_bytes(output.read(), filename="report.xlsx")

