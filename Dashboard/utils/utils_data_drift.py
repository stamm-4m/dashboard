import numpy as np
from Drift_detectors.univariate_drift import adwin_drift, psi_drift

def get_result_metric(score, data_training, data_test):
    if score == "PSI":
        psi = psi_drift(data_training, data_test)
        print(f"PSI: {psi:.4f}")
        return f"{psi:.4f}"

    if score == "ADWIN":
        stream_data = np.concatenate([data_training, data_test])
        result = adwin_drift(stream_data, delta=0.002)
        print("ADWIN result:", result)
        return result
