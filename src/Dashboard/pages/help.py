import dash_bootstrap_components as dbc
from dash import html, dcc
from Dashboard.drift_detectors_pack.drift_detectors.drift_detector import get_metadata
from Dashboard.utils.utils_help import build_drift_detector_help, build_models_help, build_navigation
from Dashboard.utils.utils_model_information import get_model_information



# Carga inicial de metadata (puede haber más secciones luego)

def help_layout(store_data=None):
    
    metadata = {}

    if not store_data:
        model_information = get_model_information(store_data.get("selected_project"))  # Get the updated model information
        metadata = {
        "Models": model_information.project_details("P0001"),
        "Drift Detectors": get_metadata(),
        # "Features": get_feature_info(),
    }
    
 

    """Vista general de la sección Help con navegación interna."""
    sections = []
    for section_name, section_data in metadata.items():
        # 🔹 ID único para scroll interno
        section_id = section_name.lower().replace(" ", "-")

        if section_name == "Drift Detectors":
            section_content = build_drift_detector_help(section_data)
        elif section_name == "Models":
            section_content = build_models_help(section_data)
        else:
            section_content = html.I("No content available yet.")

        sections.append(
            html.Div(
                [
                    html.H4(section_name, className="mt-4 mb-3 text-info"),
                    section_content,
                ],
                className="mb-5",
                id=section_id  # 👈 importante para las anclas
            )
        )

    return dbc.Container(
        [
            html.H2("Help", className="text-center mt-4 mb-4"),
            html.P("Explore the available documentation sections:", className="text-muted"),

            # 🔹 Índice de navegación
            build_navigation(metadata.keys()),

            # 🔹 Secciones completas
            html.Div(sections, id="help-content"),
        ],
        fluid=True,
        className="p-4",
    )