import re
import os
import plotly.express as px
import numpy as np
from typing import Union, Callable
from Dashboard.utils import model_information
import yaml
import logging


metric_load = []
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "../performance_estimator_pack", "performance_estimators.yaml")
    with open(filepath, 'r', encoding="utf-8") as file:
            metric_load = yaml.safe_load(file) or {}
except FileNotFoundError:
    logging.error(f"File not found: {filepath}")
except yaml.YAMLError as exc:
    logging.error(f"Error reading the YAML file: {exc}")
        


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

def calculate_mae(y_true, y_pred):
    """
    Compute Mean Absolute Error (MAE) as a single value.
    
    Formula:
        MAE = mean(|y_true - y_pred|)
    """
    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_mse(y_true, y_pred):
    """
    Compute Mean Squared Error (MSE) as a single value.
    
    Formula:
        MSE = mean((y_true - y_pred)^2)
    """
    return float(np.mean((y_true - y_pred) ** 2))


def calculate_rmse(y_true, y_pred):
    """
    Compute Root Mean Squared Error (RMSE) as a single value.
    
    Formula:
        RMSE = sqrt(mean((y_true - y_pred)^2))
    """
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

def calculate_vpd(y_true, y_pred):
    """Compute point-by-point Variation Percentage Difference."""
    return np.abs((y_pred - y_true) / y_true) * 100  # Expressed as percentage

# Metric functions that return a single value
def calculate_pcc(y_true, y_pred):
    """Compute Pearson Correlation Coefficient between two arrays."""
    return np.corrcoef(y_true, y_pred)[0, 1]

def calculate_cossim(y_true, y_pred):
    """Compute Cosine Similarity between two arrays."""
    return np.dot(y_true, y_pred) / (np.linalg.norm(y_true) * np.linalg.norm(y_pred))

def calculate_cv(y_true, y_pred):
    """
    Compute Coefficient of Variation (CV) as:
    
    CV = std(prediction difference) / mean(prediction difference)
    
    Where:
        difference = (y_pred - y_true)

    Args:
        y_true (array-like): First set of predictions (or true values).
        y_pred (array-like): Second set of predictions.
        n (int): number elements

    Returns:
        float: CV (unitless).
    """
    differences = y_pred - y_true
    mean_diff = np.mean(differences)
    if mean_diff == 0:
        return np.nan  # Avoid division by zero
    return np.abs(np.std(differences)) / mean_diff



def compute_metric(acronym: str, y_true: np.ndarray, y_pred: np.ndarray) -> Union[np.ndarray, float]:
    """
    Compute a performance metric based on its acronym.

    This function selects the appropriate metric function (point-by-point or single-value)
    based on the given acronym and computes the result using the provided true and predicted values.

    Args:
        acronym (str): The acronym of the metric to compute. Supported values:
                       - "MAE" : Mean Absolute Error (point-by-point)
                       - "MSE" : Mean Squared Error (point-by-point)
                       - "RMSE": Root Mean Squared Error (point-by-point)
                       - "VPD" : Variation Percentage Difference (point-by-point)
                       - "PCC" : Pearson Correlation Coefficient (single value)
                       - "COSSIM": Cosine Similarity (single value)
                       - "CV"  : Coefficient of Variation (single value)
        y_true (np.ndarray): Array of true values.
        y_pred (np.ndarray): Array of predicted values.
        n (int): Int elements number

    Returns:
        Union[np.ndarray, float]: The computed metric. It can be:
                                  - A NumPy array for point-by-point metrics.
                                  - A single float for single-value metrics.

    Raises:
        ValueError: If the acronym is not supported.

    Example:
        >>> y_true = np.array([1, 2, 3])
        >>> y_pred = np.array([1.1, 1.9, 3.2])
        >>> compute_metric("MAE", y_true, y_pred)
        array([0.1, 0.1, 0.2])
        >>> compute_metric("PCC", y_true, y_pred)
        0.9819805060619657
    """
    metric_map: dict[str, Callable[[np.ndarray, np.ndarray], Union[np.ndarray, float]], int] = {
        "MAE": calculate_mae,
        "MSE": calculate_mse,
        "RMSE": calculate_rmse,
        "VPD": calculate_vpd,
        "PCC": calculate_pcc,
        "COSSIM": calculate_cossim,
        "CV": calculate_cv
    }

    acronym = acronym.upper()
    if acronym not in metric_map:
        raise ValueError(f"Unsupported metric acronym: {acronym}. Supported metrics: {list(metric_map.keys())}")

    return metric_map[acronym](y_true, y_pred)


def get_performance_estimators_options():
    """
    Loads performance estimators from a YAML configuration file and returns a list of options.

    Returns:
        list: A list of dictionaries with 'label' and 'value' keys for Dash dropdowns.
    """
    estimators = set()
    global metric_load

    try:
        # Extract the list of performance estimators
        drift_detectors = metric_load.get('performance_estimators', [])
        
        if isinstance(drift_detectors, list):
            for detector in drift_detectors:
                name = detector.get('name')
                acronym = detector.get('acronym')
                if name and acronym:  # Ensure both values exist
                    estimators.add((name, acronym))
    except Exception as e:
        logging.error(f"Error processing configuration estimator: {e}")
        return []

    # Convert unique values into a list of dictionaries
    return [{"label": acronym, "value": acronym} for _, acronym in sorted(estimators)]

def load_estimator_descriptions(selected_estimator):
        global metric_load
        # Default values in case the metric is not found
        default_response = {
            "name": "Unknown Metric",
            "method": {},
            "configuration": {},
            "implementation_notes": []
        }

        if metric_load != []:
            try:
                estimators = metric_load.get('performance_estimators', [])
                
                if isinstance(estimators, list):
                    for estimator in estimators:
                        if estimator.get("acronym") == selected_estimator:
                            return {
                                "name": estimator.get("name", "Unknown Metric"),
                                "method": estimator.get("method", {}),
                                "configuration": estimator.get("configuration", {}),
                                "implementation_notes": estimator.get("implementation_notes", [])
                            }
            except Exception as e:
                logging.error(f"Error retrieving metric information {selected_estimator}: {e}")
        
        logging.warning(f"Metric not found: {selected_estimator}")
        return default_response

def reorder_dataframe_for_table(df_table, model_data_selected):
    """
    Reorders the DataFrame so that the selected model (base_name) 
    appears first in both rows and columns. Also resets index 
    and prepares columns for Dash DataTable.

    Args:
        df_table (pd.DataFrame): DataFrame with model results.
        model_data_selected (pd.Series or dict): Selected model info 
            containing at least "model_name".

    Returns:
        tuple: (df_table_reordered, columns) ready for DataTable.
    """
    base_name = model_data_selected["model_id"]  # always the model base in (0,0)

    # Reorder columns: first base, then the rest
    cols = [base_name] + [c for c in df_table.columns if c != base_name]
    df_table = df_table[cols]

    # Reorder rows: first base, then the rest
    rows = [base_name] + [r for r in df_table.index if r != base_name]
    df_table = df_table.loc[rows]

    # Reset index for DataTable
    df_table.reset_index(inplace=True)
    df_table.rename(columns={"index": "Model"}, inplace=True)

    # Define columns for Dash DataTable
    columns = [{"name": col, "id": col} for col in df_table.columns]

    return df_table, columns


