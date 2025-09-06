import numpy as np
import pandas as pd
from io import StringIO
import sys
import logging
from Dashboard.drift_detectors_pack.drift_detectors.univariate.adwin.detector import Adwin
from Dashboard.drift_detectors_pack.drift_detectors.univariate.psi.detector import PSI
from Dashboard.drift_detectors_pack.drift_detectors.univariate.ks.detector import KSDetector
from Dashboard.drift_detectors_pack.drift_detectors.multivariate.kdq_tree.detector import KDQTree
from Dashboard.drift_detectors_pack.drift_detectors.multivariate.pca_cd.detector import PCA_CD
from Dashboard.drift_detectors_pack.drift_detectors.multivariate.mmd.detector import MMDDetector

from Dashboard.drift_detectors_pack.drift_detectors.drift_detector import get_metadata

def sanitize_data(data):
    """
    Ensure data is numeric and free of NaN/Inf values.
    """
    if isinstance(data, pd.DataFrame):
        # Keep only numeric columns
        data = data.select_dtypes(include=[np.number]).to_numpy(dtype=float)
    elif isinstance(data, pd.Series):
        data = pd.to_numeric(data, errors="coerce").to_numpy(dtype=float)
    else:
        # Convert numpy arrays or lists
        data = np.array(data, dtype=float)
    
    # Replace non-finite with np.nan
    mask = ~np.isfinite(data)
    if np.any(mask):
        data[mask] = np.nan
    
    # Drop rows with NaN
    if data.ndim == 2:
        data = data[~np.isnan(data).any(axis=1)]
    else:
        data = data[~np.isnan(data)]
    
    return data

def get_result_metric(score, data_training, data_test,param_dinamic_values):
    """
    Executes the selected drift detection algorithm and returns the result.

    Parameters:
        score (str): The name of the drift detection algorithm to use.
        data_training (array-like): Reference dataset (training).
        data_test (array-like): Test dataset (incoming/production).

    Returns:
        str or list: Formatted drift score or list of detected drift indices/statuses.
    """
    logging.info(f"Received score: {score}")
    
    score = score.strip()
    params = param_dinamic_values.get(score, {})
    print(f"Paremeters {params} to {score}")
    try:
        # PSI (Population Stability Index)
        if score == "PSI":
            bins = int(params.get('bins') or 10)
            epsilon = float(params.get('epsilon', 1e-8))
            threshold = float(params.get('threshold') or 0.05)
            logging.info("Calculating PSI (Population Stability Index)...")
            psi = PSI(threshold=threshold)
            result = psi.calculate(data_training, data_test,bins,epsilon)
            logging.info(f"PSI result: {result}")
            return result

        # ADWIN (ADaptive WINdowing)
        elif score == "ADWIN":
            delta = float(params.get('delta') or 0.002)
            logging.info("Calculating ADWIN (ADaptive WINdowing)...")
            adwin = Adwin()
            result = adwin.calculate(data_test, delta)
            logging.info(f"ADWIN result: {result}")
            return result

        # Kolmogorov-Smirnov Detector
        elif score == "KS":
            alpha = float(params.get('alpha') or 0.05)
            logging.info("Calculating KSDetector (Kolmogorov-Smirnov Test)...")
            ks = KSDetector()
            result = ks.calculate(data_training, data_test,alpha)
            logging.info(f"KS result: {result}")
            return result

        # KDQTree Detector
        elif score == "KDQ":
            k_neighbors = float(params.get('k_neighbors') or 5)
            ks_method = str(params.get('ks_method') or "asymp")
            alpha = float(params.get('alpha') or 0.25)
            logging.info("Calculating KDQTree...")
            data_training_reshaped = np.array(data_training).reshape(-1, 1)
            data_test_reshaped = np.array(data_test).reshape(-1, 1)
            data_test_reshaped = sanitize_data(data_test_reshaped)
            data_training_reshaped = sanitize_data(data_training_reshaped)
            detector = KDQTree(data_training_reshaped,
                               k_neighbors,
                               ks_method,
                               alpha)
            result = detector.calculate(data_test_reshaped)
            logging.info(f"KDQTree result: {result}")
            return result
        
        # MMDDetector Detector
        elif score == "MMD":
            gamma = float(params.get('gamma') or 1.0)
            threshold = float(params.get('threshold') or 0.05)
            logging.info("Calculating MMDDetector...")
            data_training_reshaped = np.array(data_training).reshape(-1, 1)
            data_test_reshaped = np.array(data_test).reshape(-1, 1)
            detector = MMDDetector(gamma=gamma, threshold=threshold)
            detector.set_reference_data(data_training_reshaped)

            result = detector.calculate(test_data=data_test_reshaped)
            logging.info(f"MMDDetector result: {result}")
            return result
        # PCA-CD Change Detection 
        elif score == "PCA-CD":
            n_components = int(params.get('n_components') or 2)
            csd_threshold = float(params.get('csd_threshold') or 0.1)
            kl_threshold = float(params.get('kl_threshold') or 0.05)
            logging.info("Calculating PCA-CD Detector...")
            data_training_reshaped = np.array(data_training).reshape(-1, 1)
            data_test_reshaped = np.array(data_test).reshape(-1, 1)

            detector = PCA_CD(n_components=n_components,csd_threshold=csd_threshold, kl_threshold=kl_threshold)
            detector.set_reference_data(data_training_reshaped)

            result = detector.calculate(test_data=data_test_reshaped)
            logging.info(f"PCA-CD Detector result: {result}")
            return result
        
        # Unknown algorithm
        else:
            logging.error(f"Unknown score type: {score}")
            raise ValueError(f"Unknown score type: {score}")

    except Exception as e:
        logging.error(f"Error occurred while processing '{score}': {e}", exc_info=True)
        return None

# Function to get the parameter information and description of drift detectors
def get_detector_description(detector_selected):
    # Log the input parameter for debugging purposes
    print("detector_selected",detector_selected)
    logging.debug(f"Received detector: {detector_selected}")
    default_response = {
            "name": "Unknown Metric",
            "thresholds": {"low": "N/A", "moderate": "N/A", "high": "N/A"},
            "configuration": {}
    }
    detector_selected = detector_selected.strip()
    md_drift_detector = {}

    try:
        #find on all metadata detectors    
        #detector_description = load_estimator_descriptions(detector_selected)
        # Handle PSI (Population Stability Index)
        if detector_selected == "PSI":
            psi = PSI()
            md_drift_detector = psi.metadata
            
        # Handle ADWIN (ADaptive WINdowing)
        elif detector_selected == "ADWIN":
            adwin = Adwin()
            md_drift_detector = adwin.metadata
            
        # Handle Kolmogorov-Smirnov detector
        elif detector_selected == "KS":
            ks = KSDetector()
            md_drift_detector = ks.metadata
        
        # Handle  Maximum Mean Discrepancy (MMD) Drift Detector.
        elif detector_selected == "MMD":
            mmd = MMDDetector()
            md_drift_detector = mmd.metadata
        
        # Handle Principal Component Analysis to monitor structural changes in the data (PCA-CD) Drift Detector.
        elif detector_selected == "PCA-CD":
            mmd = PCA_CD()
            md_drift_detector = mmd.metadata

        # Handle KDQTree detector (requires input data in shape [n_samples, n_features])
        elif detector_selected == "KDQ":
            # Example data transformation for compatibility (replace with actual data)
            detector = KDQTree()
            md_drift_detector = detector.metadata
        # Handle unknown detector names
        else:
            logging.error(f"Unknown detector type: {detector_selected}")
            raise ValueError(f"Unknown detector type: {detector_selected}")
        
        detector_description = load_estimator_descriptions(detector_selected,md_drift_detector)

        return {
                "name": detector_description.get("name", "Unknown Metric"),
                "thresholds": detector_description.get("thresholds", default_response["thresholds"]),
                "configuration": detector_description.get("configuration", {})
            }

        

    except Exception as e:
        # Log the exception with full traceback for easier debugging
        logging.error(f"Error occurred while processing {detector_selected}: {e}", exc_info=True)
        return None

def get_metrics_score_options():
    """
    Retrieve metric score options from metadata for UI dropdowns.

    This method loads metadata definitions (e.g., for monitoring or model evaluation),
    extracts their acronyms and associated keys, and prepares a list of dictionaries
    to be used as label-value options in a UI component like a dropdown menu.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with "label" (acronym) and "value" (key)
        sorted alphabetically by acronym. Each entry represents a selectable metric option.

    Example:
        [{'label': 'PSI', 'value': 'population_stability_index'},
         {'label': 'KL', 'value': 'kullback_leibler_divergence'}]
    """
    try:
        metrics = []
        mds = get_metadata()
        for name, md in mds.items():
            metrics.append((md["acronym"], name))
    except Exception as e:
        logging.error(f"Error processing metadata score metrics: {e}")

    return [{"label": k, "value": k} for k, v in sorted(metrics)]

def load_estimator_descriptions(selected_estimator, metadata_dict=None):
    """
    Retrieve detailed description of a selected drift detector.

    Args:
        selected_estimator (str): Acronym of the drift detector (e.g., 'ADWIN').
        metadata_dict (dict, optional): 
            - If it's a dict of detectors: {'ADWIN': {...}, 'DDM': {...}, ...}
            - If it's a single detector dict: {...}
            If not provided, will fallback to get_metadata().

    Returns:
        dict: A dictionary with the following keys:
              - "name": Full name of the detector.
              - "method": Description of the detection method.
              - "configuration": Dict of parameter descriptions.
              - "implementation_notes": Info from 'output' → 'fields'.
    """
    default_response = {
        "name": "Unknown Metric",
        "method": {},
        "configuration": {},
        "implementation_notes": []
    }

    try:
        # fallback
        if metadata_dict is None:
            metadata_dict = get_metadata()
        
        # CASE 1: metadata_dict is the dict of a single detector (e.g., 'ADWIN')
        if metadata_dict.get("acronym") == selected_estimator:
            detector = metadata_dict
        
        # CASE 2: metadata_dict is a dict of detectors
        else:
            detector = metadata_dict.get(selected_estimator)
        print("detector",detector)
        if detector:
            return {
                "name": detector.get("name", "Unknown Metric"),
                "method": detector.get("description", {}),
                "configuration": detector.get("parameters", {}),
                "implementation_notes": detector.get("output", {}).get("fields", {})
            }

    except Exception as e:
        logging.error(f"Error retrieving information for {selected_estimator}: {e}")

    logging.warning(f"Detector not found: {selected_estimator}")
    return default_response
        
def parse_markdown_table(markdown_str: str) -> pd.DataFrame:
    # Convert the markdown string to a DataFrame
    df = pd.read_csv(StringIO(markdown_str), sep="|", engine="python", skipinitialspace=True)
    df = df.drop(columns=[""], errors="ignore")  # Drop empty columns if any
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Drop unnamed columns
    
    # Drop the separator row (row that contains only dashes)
    df = df.drop(index=0).reset_index(drop=True)
    df.columns = df.columns.str.strip()  # Limpia espacios

    return df

