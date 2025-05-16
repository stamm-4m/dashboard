import dash
from utils import model_information
from utils.utils_maintenance import get_maintenance_layout

def maintenance_layout():

    # Load model options dynamically for layout
    model_options = model_information.get_model_name_options()

    # Return only the content specific to the maintenance page
    return get_maintenance_layout(model_options)