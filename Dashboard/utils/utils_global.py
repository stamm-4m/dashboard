import plotly.graph_objects as go
import re

disabled_figure = {
            "data": [],
            "layout": go.Layout(
                xaxis={"title": "X Axis", "visible": False},
                yaxis={"title": "Y Axis", "visible": False},
                annotations=[
                    {
                        "text": "Graph Disabled",
                        "xref": "paper",
                        "yref": "paper",
                        "showarrow": False,
                        "font": {"size": 20, "color": "gray"},
                    }
                ],
                plot_bgcolor="lightgray",  # background gray to effect "disabilabled"
                paper_bgcolor="lightgray",
            ),
        } 

def generate_prediction_name(model_file):
    # Regular expression to extract the text between the last two underscores '_'
    match = re.search(r'_([^_]*)\.pkl$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .pkl
        return f"pred_penicillin_{model_type}"
    
    match = re.search(r'_([^_]*)\.keras$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .keras
        return f"pred_penicillin_{model_type}"
    
    match = re.search(r'_([^_]*)\.rds$', model_file)
    
    if match:
        model_type = match.group(1)  # Extracts the part before .rds
        return f"pred_penicillin_{model_type}"
    
    return "penicillin_concentration"
