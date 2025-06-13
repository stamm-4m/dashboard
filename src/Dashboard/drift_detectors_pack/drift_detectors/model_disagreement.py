import os
import yaml
import numpy as np
from typing import Callable, Dict, Any

curr_dir = os.path.dirname(os.path.realpath(__file__))
METADATA_MODEL_DISAGREEMENT = os.path.join(curr_dir,"model_disagreement.yaml")

class ModelDisagreementMetrics:
    """
    Represents a metric for measuring disagreement between two model predictions.
    """
    def __init__(self, name: str, acronym: str, func: Callable):
        self.name = name
        self.acronym = acronym
        self.func = func

    def compute(self, pred1: np.ndarray, pred2: np.ndarray) -> float:
        """
        Compute the disagreement value using the selected metric.
        """
        if len(pred1) != len(pred2):
            raise ValueError("Prediction arrays must have the same length")
        return self.func(pred1, pred2)


class DisagreementMetricLoader:
    """
    Loads metric configuration and functions from YAML and provides access to metadata and callable objects.
    """
    def __init__(self, yaml_path: str = METADATA_MODEL_DISAGREEMENT):
        self.yaml_path = yaml_path
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)

    def get_metric(self, acronym: str) -> ModelDisagreementMetrics:
        """
        Returns a ModelDisagreementMetrics object based on acronym found in YAML.
        """
        for item in self.data['drift_detector']:
            if item['acronym'] == acronym:
                name = item['name']
                func = self.get_function(acronym)
                if func:
                    return ModelDisagreementMetrics(name, acronym, func)
                else:
                    raise ValueError(f"No function defined for acronym: {acronym}")
        raise ValueError(f"Metric with acronym '{acronym}' not found in YAML file")

    def get_metadata(self, acronym: str) -> Dict[str, Any]:
        """
        Returns metadata dictionary for a given metric acronym.
        """
        for item in self.data['drift_detector']:
            if item['acronym'] == acronym:
                return item
        raise ValueError(f"Metadata for metric acronym '{acronym}' not found in YAML file")

    @staticmethod
    def get_function(acronym: str) -> Callable:
        """
        Returns the metric function corresponding to the given acronym.
        """
        return {
            "MAE": lambda x, y: np.mean(np.abs(x - y)),
            "MSE": lambda x, y: np.mean((x - y) ** 2),
            "RMSE": lambda x, y: np.sqrt(np.mean((x - y) ** 2)),
            "PCC": lambda x, y: np.corrcoef(x, y)[0, 1] if len(x) > 1 else np.nan,
            "CV": lambda x, y: np.std(x - y) / np.mean(np.abs(x - y)) if np.mean(np.abs(x - y)) != 0 else np.nan,
        }.get(acronym, None)





