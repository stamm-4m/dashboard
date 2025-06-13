import numpy as np
from drift_detectors.drift_detector import ScoreBasedDriftDetector, MultivariateDriftDetector
from drift_detectors.utility.drift_detection_output import DriftDetectionResult
import numpy as np
from scipy.spatial import KDTree
from scipy.stats import ks_2samp

class KDQTree(ScoreBasedDriftDetector, MultivariateDriftDetector):
    def __init__(self, reference_data,k_neighbors=5, ks_method='auto'):
        """
        KDQ-based Concept Drift Detector using Kulldorff Spatial Scan Statistic (KSS).
        
        Parameters:
        - data (np.ndarray): Historical reference data (n_samples, n_features).
        - k_neighbors (int): Number of nearest neighbors to use around each point.
        - ks_method (str): Method for ks_2samp, either 'auto', 'exact', or 'asymp'.
        """
        self.k_neighbors = k_neighbors
        self.ks_method = ks_method
        self.reference_data = reference_data
        self.tree_ref = KDTree(reference_data)

        super().__init__()


    def calculate(self, test_data) -> DriftDetectionResult:
        """
        Compare test data to reference data using KSS approach.

        Parameters:
        - test_data (np.ndarray): New incoming data to evaluate for drift.

        Returns:
        - results (DriftDetectionResult): Average p-value from KS tests. Lower means more likely drift.
        """
        tree_test = KDTree(test_data)

        p_values = []
        for i in range(len(self.reference_data)):
            ref_neighbors = self.reference_data[self.tree_ref.query(self.reference_data[i], 
                                                                    k=self.k_neighbors)[1]]
            test_neighbors = test_data[tree_test.query(test_data[i], k=self.k_neighbors)[1]]
            _, p_val = ks_2samp(
                ref_neighbors[:, 0],
                test_neighbors[:, 0],
                method=self.ks_method
            )
            p_values.append(p_val)
        return DriftDetectionResult(p_values,np.mean(p_values))
