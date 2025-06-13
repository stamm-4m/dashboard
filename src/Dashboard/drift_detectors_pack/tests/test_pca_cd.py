import unittest
import sys
import os
import numpy as np
sys.path.insert(0, os.path.join(".."))

import numpy as np

from drift_detectors.multivariate.pca_cd import PCA_CD

class TestPCA_CD(unittest.TestCase):
    def test_what(self):
        # Set random seed for reproducibility
        np.random.seed(42)

        #%%
        # 1. Generate Reference Data (no drift)
        reference_data = np.random.normal(loc=0.0, scale=1.0, size=(200, 5))  # Mean 0

        # 2. Generate Test Data (progressive drift)
        test_data = []
        for i in range(200):
            # Mean increases linearly from 0 to 3
            mean_shift = (i / 200) * 3.0
            sample = np.random.normal(loc=mean_shift, scale=1.0, size=(1, 5))
            test_data.append(sample.flatten())
        test_data = np.array(test_data)

        #%%
        # 3. Setup pca_cd
        detector = PCA_CD(n_components=2, csd_threshold=0.1, kl_threshold=0.05)

        # Set reference window
        detector.reference_window = reference_data.tolist()

        #%%
        # 4. Test for drift batch by batch
        print("\nTesting progressive drift...")
        detector.test_window = []  # Clear
        batch_size = 20  # every 20 samples we test

        statuses = []
        scores = []

        for i, row in enumerate(test_data):
            detector.test_window.append(row)
            if (i+1) % batch_size == 0:
                status, score = detector.calculate(row)
                statuses.append(status)
                scores.append(score)
                print(f"Batch {(i+1)//batch_size} -> Status: {status}, Score: {score}")




if __name__ == "__main__":
    unittest.main()

