from scipy.stats import ks_2samp
from drift_detectors.drift_detector import ScoreBasedDriftDetector
from drift_detectors.utility.drift_detection_output import DriftDetectionResult
import numpy as np

class KSDetector(ScoreBasedDriftDetector):
    def calculate(self, reference_data: np.ndarray, 
                  test_data: np.ndarray, 
                  alpha: float = 0.05, **kwargs) -> DriftDetectionResult:
        stat, p_value = ks_2samp(reference_data, test_data)
        drift = p_value < alpha
        return self._produce_result(score=stat, threshold=None, alpha=alpha, 
                                    p_value=p_value, drift_by_pvalue=drift)
