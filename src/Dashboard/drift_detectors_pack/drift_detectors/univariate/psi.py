import numpy as np

from drift_detectors.drift_detector import ScoreBasedDriftDetector
from drift_detectors.utility.drift_detection_output import DriftDetectionResult

class PSI(ScoreBasedDriftDetector):
    def calculate(self, reference_data: np.ndarray, 
                  test_data: np.ndarray, 
                  bins: int = 10, epsilon: float = 1e-8) -> DriftDetectionResult:
        """
        Calculate the Population Stability Index (PSI).

        Parameters:
            reference_data (np.ndarray): Historical or training data (1D).
            test_data (np.ndarray): Current or new data (1D).
            bins (int): Number of histogram bins.
            epsilon (float): Small value to avoid log(0).

        Returns:
            DriftDetectionResult: Includes PSI score and whether drift was detected.
        """
        reference_data = np.asarray(reference_data).flatten()
        test_data = np.asarray(test_data).flatten()

        bin_edges = np.linspace(min(reference_data.min(), test_data.min()),
                                max(reference_data.max(), test_data.max()),
                                bins + 1)

        ref_counts, _ = np.histogram(reference_data, bins=bin_edges)
        test_counts, _ = np.histogram(test_data, bins=bin_edges)

        ref_probs = np.clip(ref_counts / ref_counts.sum(), epsilon, 1)
        test_probs = np.clip(test_counts / test_counts.sum(), epsilon, 1)

        psi = np.sum((test_probs - ref_probs) * np.log(test_probs / ref_probs))

        return self._produce_result(psi, bins=bins, epsilon=epsilon)
