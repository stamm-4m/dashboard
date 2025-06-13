import numpy as np
import logging
from Dashboard.drift_detectors_pack.drift_detectors.univariate.adwin import Adwin
from Dashboard.drift_detectors_pack.drift_detectors.univariate.psi import PSI
from Dashboard.drift_detectors_pack.drift_detectors.univariate.ks import KSDetector
from Dashboard.drift_detectors_pack.drift_detectors.multivariate.KDQ_tree import KDQTree
from Dashboard.drift_detectors_pack.drift_detectors.multivariate.pca_cd import PCA_CD



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
            bins = params.get('bins') or 10
            epsilon = float(params.get('epsilon', 1e-8))
            logging.info("Calculating PSI (Population Stability Index)...")
            psi = PSI()
            result = psi.calculate(data_training, data_test,bins,epsilon)
            logging.info(f"PSI score: {result.drift_score:.4f}")
            return f"{result.drift_score:.4f}"

        # PCA-based Change Detection (PCA_CD)
        elif score == "PCA_CD":
            logging.info("Calculating PCA-based Change Detection (PCA-CD)...")
            detector = PCA_CD(n_components=2, csd_threshold=0.1, kl_threshold=0.05)
            detector.reference_window = data_training.tolist()

            batch_size = 20
            detector.test_window = []
            statuses = []
            scores = []

            for i, row in enumerate(data_test):
                detector.test_window.append(row)
                if (i + 1) % batch_size == 0:
                    status, score_val = detector.calculate(row)
                    statuses.append(status)
                    scores.append(score_val)
                    logging.info(f"Batch {(i + 1) // batch_size}: Status={status}, Score={score_val}")

            return f"Statuses: {statuses}, Scores: {scores}"

        # ADWIN (ADaptive WINdowing)
        elif score == "Adwin":
            delta = params.get('delta') or 0.002
            logging.info("Calculating ADWIN (ADaptive WINdowing)...")
            adwin = Adwin()
            result = adwin.calculate(data_test, delta)
            logging.info(f"ADWIN drift indices: {result.drift_indices}")
            return result.drift_indices

        # Kolmogorov-Smirnov Detector
        elif score == "KSDetector":
            alpha = params.get('alpha') or 0.05
            logging.info("Calculating KSDetector (Kolmogorov-Smirnov Test)...")
            ks = KSDetector()
            result = ks.calculate(data_training, data_test,alpha)
            logging.info(f"KS result: {result}")
            return result

        # KDQTree Detector
        elif score == "KDQTree":
            logging.info("Calculating KDQTree...")
            data_training_reshaped = np.array(data_training).reshape(-1, 1)
            data_test_reshaped = np.array(data_test).reshape(-1, 1)
            detector = KDQTree(data_training_reshaped,
                               k_neighbors=5,
                               ks_method='asymp')
            result = detector.calculate(data_test_reshaped)
            logging.info(f"KDQTree drift score: {result.drift_score:.4f}")
            return f"{result.drift_score:.4f}"

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
    logging.info(f"Received detector: {detector_selected}")
    default_response = {
            "name": "Unknown Metric",
            "thresholds": {"low": "N/A", "moderate": "N/A", "high": "N/A"},
            "configuration": {}
    }
    detector_selected = detector_selected.strip()

    try:
        # Handle PSI (Population Stability Index)
        if detector_selected == "PSI":
            psi = PSI()
            drift_detector = psi.get_algorithm_info()

        # Handle PCA Change Detection
        elif detector_selected == "PCA_CD":
            detector = PCA_CD(n_components=2, csd_threshold=0.1, kl_threshold=0.05)
            drift_detector = detector.get_algorithm_info()

        # Handle ADWIN (ADaptive WINdowing)
        elif detector_selected == "Adwin":
            adwin = Adwin()
            drift_detector = adwin.get_algorithm_info()

        # Handle Kolmogorov-Smirnov detector
        elif detector_selected == "KSDetector":
            ks = KSDetector()
            drift_detector = ks.get_algorithm_info()

        # Handle KDQTree detector (requires input data in shape [n_samples, n_features])
        elif detector_selected == "KDQTree":
            # Example data transformation for compatibility (replace with actual data)
            data_training_reshaped = np.array(np.random.rand(50)).reshape(-1, 1)
            
            detector = KDQTree(data_training_reshaped,
                               k_neighbors=5,
                               ks_method='asymp')
            drift_detector = detector.get_algorithm_info()
        # Handle unknown detector names
        else:
            logging.error(f"Unknown detector type: {detector_selected}")
            raise ValueError(f"Unknown detector type: {detector_selected}")
        
        return {
                "name": drift_detector.get("name", "Unknown Metric"),
                "thresholds": drift_detector.get("thresholds", default_response["thresholds"]),
                "configuration": drift_detector.get("configuration", {})
            }

        

    except Exception as e:
        # Log the exception with full traceback for easier debugging
        logging.error(f"Error occurred while processing {detector_selected}: {e}", exc_info=True)
        return None
