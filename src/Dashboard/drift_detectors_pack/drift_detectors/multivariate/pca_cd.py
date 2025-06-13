import numpy as np
from sklearn.decomposition import PCA
from scipy.stats import entropy

from drift_detectors.drift_detector import ScoreBasedDriftDetector, MultivariateDriftDetector
from drift_detectors.utility.drift_detection_output import DriftDetectionResult

class PCA_CD(ScoreBasedDriftDetector, MultivariateDriftDetector):
    def __init__(self, n_components=2, csd_threshold=0.1, 
                 kl_threshold=0.05,reference_window = None):
        """
        Initialize the PCA-based Concept Drift detector.

        Parameters:
        - n_components (int): Number of PCA components to use.
        - csd_threshold (float): Threshold for detecting mean shift (CSD) drift.
        - kl_threshold (float): Threshold for detecting variance shift (KL divergence) drift.
        """
        super().__init__()
        self._n_components = n_components
        self._csd_threshold = csd_threshold
        self._kl_threshold = kl_threshold
        if reference_window is None:
            self._reference_window = []
        else:
            self._reference_window = reference_window
        self._test_window = []
        

    def set_reference_window(self,window):
        self._reference_window = window

    def calculate(self, new_data) -> DriftDetectionResult:
        """
        Add new data to the test window and check for drift.

        Parameters:
        - new_data (np.ndarray or list): New incoming data point.

        Returns:
        - status (str): "not_ready", "stable", "moderate", or "drift"
        - score (float or None): Computed drift score, if available.
        """        
        self._test_window.append(new_data)
        
        # Check if both windows have data to compare
        if len(self._reference_window) == 0 or len(self._test_window) == 0:
            return "not_ready", None
        
        # Convert windows to numpy arrays
        ref = np.array(self._reference_window)
        test = np.array(self._test_window)

        # Project reference and test data onto their PCA spaces
        ref_proj, _ = self._fit_pca(ref)
        test_proj, _ = self._fit_pca(test)
        
        # Compute drift score
        score = self._compute_drift_score(ref_proj, test_proj)
        return self._produce_result(score,self._kl_threshold)

        
    def _fit_pca(self, data):
        """
        Fit PCA on input data and return the projected components.

        Parameters:
        - data (np.ndarray): Input data matrix (n_samples, n_features)

        Returns:
        - components (np.ndarray): Transformed data in PCA space.
        - pca (PCA object): Trained PCA model.
        """
        pca = PCA(n_components=self._n_components)
        components = pca.fit_transform(data)
        return components, pca

    def _symmetric_kl_divergence(self, p, q):
        """
        Compute symmetric Kullback-Leibler (KL) divergence between two distributions (p and q).

        Parameters:
        - p (np.ndarray): First distribution (e.g., variances).
        - q (np.ndarray): Second distribution.

        Returns:
        - float: Symmetric KL divergence score.
        """        
        # Clip to avoid division by zero or log(0)        
        p = np.clip(p, 1e-8, None)
        q = np.clip(q, 1e-8, None)
        # Symmetrised KL: (KL(p||q) + KL(q||p)) / 2        
        return 0.5 * (entropy(p, q) + entropy(q, p))

    def _compute_drift_score(self, ref_components, test_components):
        """
        Compute a drift score based on mean and variance shifts in PCA space.

        Parameters:
        - ref_components (np.ndarray): Reference data projected onto PCA space.
        - test_components (np.ndarray): Test data projected onto PCA space.

        Returns:
        - float: Combined drift score (normalised).
        """
        
        # Centered Squared Distance (CSD): Shift in the mean position        
        csd = np.sum((np.mean(test_components, axis=0) - np.mean(ref_components, axis=0))**2)
        
        # Symmetric KL divergence: Shift in variance structure
        kl_score = self._symmetric_kl_divergence(
            np.var(ref_components, axis=0),
            np.var(test_components, axis=0)
        )
        
        # Take the maximum normalised score        
        score = max(csd / self._csd_threshold, kl_score / self._kl_threshold)
        return score
