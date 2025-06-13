import unittest
import sys
import os
sys.path.insert(0, os.path.join(".."))

import numpy as np
from drift_detectors.multivariate.KDQ_tree import KDQTree

class TestKDQTree(unittest.TestCase):
    def setUp(self):
        pass

    def test_calculate(self):
        np.random.seed(42)
        reference_data = np.random.rand(100, 2)
        test_data = np.random.rand(100, 2) + 0.2

        detector = detector = KDQTree(reference_data,
                                      k_neighbors=5, 
                                      ks_method='asymp')
        score = detector.calculate(test_data)
        self.assertTrue(score.drift_score > 0.05)
        self.assertFalse(score.drift_detected)



if __name__ == "__main__":
    unittest.main()

