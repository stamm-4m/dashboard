import unittest
import numpy as np

from drift_detectors.model_disagreement import DisagreementMetricLoader
class TestAdwin(unittest.TestCase):

    def setUp(self):
        pass

    def test_drift_detection(self):
        # Simulated predictions (100 points each)
        pred1 = np.random.rand(100)
        pred2 = pred1 + np.random.normal(0, 0.05, size=100)

        # Load MAE metric
        loader = DisagreementMetricLoader()
        metric = loader.get_metric("PCC")
        
        # Display metadata
        metadata = loader.get_metadata("PCC")
        print("Metadata:", metadata)    
        
        # Compute MAE metric
        value = metric.compute(pred1, pred2)
        print(f"{metric.name} ({metric.acronym}): {value:.4f}")


if __name__ == "__main__":
    unittest.main()