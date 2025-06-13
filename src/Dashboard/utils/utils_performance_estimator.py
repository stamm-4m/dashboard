import re
import plotly.express as px
import numpy as np
from Dashboard.utils import model_information

color_palette = px.colors.qualitative.Dark24
color_index = 0  # Global index to select colors from the list

def get_next_color():
    """ Retrieves a different color each time it is called """
    global color_index
    color = color_palette[color_index % len(color_palette)]  # Loops if colors run out
    color_index += 1  # Advances the index for the next line
    return color

# Calls the function again to read  'Models
def reload_models():
    model_information.configurations = []
    model_information.load_all_models()