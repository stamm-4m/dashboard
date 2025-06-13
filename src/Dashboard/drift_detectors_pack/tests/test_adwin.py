import unittest
import numpy as np

from drift_detectors.univariate.adwin import Adwin
from drift_detectors.utility.drift_detection_output import DriftDetectionResult


class TestAdwin(unittest.TestCase):

    def setUp(self):
        self.detector = Adwin()

    def test_output_type(self):
        """Ensure ADWIN returns a DriftDetectionResult object."""
        data = np.random.normal(0, 1, 100)
        result = self.detector.calculate(data)
        self.assertIsInstance(result, DriftDetectionResult)

    def test_drift_detection(self):
        """ADWIN should detect drift in a data stream with a clear shift."""
        np.random.seed(42)
        stream_data = np.concatenate([
            np.random.normal(0, 1, 500),
            np.random.normal(2, 1, 500)
        ])
        result = self.detector.calculate(stream_data, delta=0.002)

        self.assertTrue(result.drift_detected)
        self.assertIsInstance(result.drift_indices, list)
        self.assertGreater(len(result.drift_indices), 0)

    def test_no_drift(self):
        """ADWIN should not detect drift in stable data."""
        np.random.seed(42)
        stream_data = np.random.normal(0, 1, 1000)
        result = self.detector.calculate(stream_data, delta=0.002)

        self.assertFalse(result.drift_detected)
        self.assertEqual(result.drift_indices, [])


if __name__ == "__main__":
    unittest.main()