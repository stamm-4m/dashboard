import dash
from utils.model_config_loader import ModelConfigLoader
from utils.utils_maintenance import get_maintenance_layout

def maintenance_layout():

    # Load model options dynamically for layout
    config_loader = ModelConfigLoader()
    config_loader.load_multiple_yaml_files('../ML_Repository')
    model_options = config_loader.get_model_name_options()

    # Return only the content specific to the maintenance page
    return get_maintenance_layout(model_options)