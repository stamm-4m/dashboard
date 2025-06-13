import re

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
