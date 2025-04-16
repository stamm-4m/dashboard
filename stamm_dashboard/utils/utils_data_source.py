
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
    ]
}

def get_variable_category(variable_name):
        """Returns the category of a variable based on predefined mappings."""
        variable_name = variable_name.lower()  # Ensure case-insensitivity
        for category, variables in variable_categories.items():
            if variable_name in [v.lower() for v in variables]:
                return category.replace("_", " ").capitalize()
        return "Unknown"