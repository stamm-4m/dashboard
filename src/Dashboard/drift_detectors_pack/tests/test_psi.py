import unittest
import numpy as np
from drift_detectors.univariate.psi import PSI
from drift_detectors.utility.drift_detection_output import DriftDetectionResult

class TestPSI(unittest.TestCase):
    def setUp(self):
        self.detector = PSI()

    def test_calculate(self):
        np.random.seed(42)
        ref_data = np.random.normal(0, 1, 1000)
        test_data = np.random.normal(0.5, 1, 1000)
        result = self.detector.calculate(ref_data, test_data)
        self.assertIsInstance(result, DriftDetectionResult,type(result))
        self.assertGreater(result.drift_score, 0)
        self.assertTrue(result.drift_detected)
        print(f"PSI value: {result.drift_score:.4f}")

    def test_no_drift(self):
        np.random.seed(42)
        ref_data = np.random.normal(0, 1, 1000)
        test_data = np.random.normal(0, 1, 1000)
        result = self.detector.calculate(ref_data, test_data)
        self.assertLess(result.drift_score, 0.25)
        self.assertFalse(result.drift_detected)

    def test_get_algorithm_info(self):
        metadata = self.detector.get_algorithm_info()
        if metadata:
            self.assertEqual(metadata.get("name"), "Population Stability Index")
            self.assertIn("parameters", metadata)
            self.assertIn("bins", metadata["parameters"])
        else:
            self.skipTest("No metadata file found.")

if __name__ == "__main__":
    unittest.main()