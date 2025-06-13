import numpy as np
from river.drift import ADWIN as AW_ALG

from drift_detectors.drift_detector import StreamDriftDetector
from drift_detectors.utility.drift_detection_output import DriftDetectionResult


class Adwin(StreamDriftDetector):
    def calculate(self, test_data: np.ndarray, delta: float = 0.002) -> DriftDetectionResult:
        """
        Run ADWIN drift detection on a univariate sequence.

        Parameters:
            test_data (np.ndarray): Streaming sequence (1D).
            delta (float): Confidence value, smaller means stricter.

        Returns:
            DriftDetectionResult: Drift detection result including indices and count.
        """
        detector = AW_ALG(delta=delta)
        drift_points = []

        for i, value in enumerate(test_data):
            detector.update(value)
            if detector.drift_detected:
                drift_points.append(i)

        return self._produce_result(drift_points, delta=delta)