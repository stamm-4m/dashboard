import dash.html as html
import dash_bootstrap_components as dbc
import re

# Mapping of variables to categories
variable_categories = {
    "sensor": [
        "air_head_pressure", "dissolved_oxygen_concentration", "pH", 
        "temperature", "generated_heat", "CO2_percent_in_off_gas",
        "oxygen_uptake_rate", "oxygen_in_percent_in_off_gas",
        "carbon_evolution_rate"
    ],
    "actuator": [
        "aeration_rate", "agitator", "sugar_feed_rate", "acid_flow_rate", "base_flow_rate", 
        "heating/cooling_water_flow_rate", "heating_water_flow_rate", "water_for_injection/dilution",
        "dumped_broth_flow", "substrate_concentration", "PAA_flow", "oil_flow", "ammonia_shots"
    ],
    "computed_variable": [
        "vessel_volume", "vessel_weight"
    ],
    "soft_sensor": [
        "penicillin_concentration"
    ],
    "offline_measurement":[
        "PAA_concentration", "NH3_concentration", "offline_penicillin_concentration",
        "offline_biomass_concentration", "viscosity"
    ],
    "Time":[
        "experiment_time"
    ],
    "ID":[
        "Batch"
    ],
    "Penicillin prediction": "^pred_penicillin_.*$"
}

def get_variable_category(variable_name):
    """Returns the category of a variable based on predefined mappings.
    Handles exact matches and regex-based dynamic categories.
    """
    variable_name = variable_name.lower().strip()  # Normalize name
    
    for category, mapping in variable_categories.items():
        if isinstance(mapping, list):
            # Exact match in a predefined list
            if variable_name in [v.lower() for v in mapping]:
                return category.replace("_", " ").capitalize()
        elif isinstance(mapping, str):
            # Regex match for dynamic categories
            if re.match(mapping, variable_name):
                return category.replace("_", " ").capitalize()
    
    return "Unknown"

def generate_projects_details_view(data):
    if not data:
        return html.P("The information projects was not found.", style={'textAlign': 'center'})

    description = data.get('description', [])
    
    return (
        html.Div(
            description,
            style={
                "height": "300px",  # Altura fija del contenedor
                "overflowY": "scroll",  # Scroll vertical
                "border": "1px solid #ccc",
                "padding": "10px",
                "backgroundColor": "#f8f9fa"
            }
        )
    )
