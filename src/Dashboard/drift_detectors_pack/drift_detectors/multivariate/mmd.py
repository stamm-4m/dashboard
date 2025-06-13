from sklearn.metrics.pairwise import rbf_kernel
from drift_detectors.drift_detector import ScoreBasedDriftDetector, MultivariateDriftDetector
from drift_detectors.utility.drift_detection_output import DriftDetectionResult
import numpy as np

class MMDDetector(ScoreBasedDriftDetector, MultivariateDriftDetector):
    def calculate(self, reference_data: np.ndarray, 
                  test_data: np.ndarray, 
                  gamma: float = 1.0, **kwargs) -> DriftDetectionResult:
        XX = rbf_kernel(reference_data, reference_data, gamma=gamma)
        YY = rbf_kernel(test_data, test_data, gamma=gamma)
        XY = rbf_kernel(reference_data, test_data, gamma=gamma)
        mmd = XX.mean() + YY.mean() - 2 * XY.mean()
        return self._produce_result(mmd, gamma=gamma)