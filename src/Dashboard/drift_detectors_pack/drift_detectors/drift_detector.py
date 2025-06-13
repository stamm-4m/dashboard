from abc import ABC, abstractmethod
from typing import List
import yaml
import os

from drift_detectors.utility.drift_detection_output import DriftDetectionResult

class DriftDetector(ABC):
    @abstractmethod
    def calculate(self, *args, **kwargs) -> DriftDetectionResult:
        pass

    def get_algorithm_info(self) -> dict:
        path = os.path.join(os.path.dirname(__file__), "algorithm_metadata.yaml")
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            metadata = yaml.safe_load(f)
        return metadata.get(self.__class__.__name__, {})


class BatchDriftDetector(DriftDetector):
    """Base class for detectors that work on static reference + test data."""
    pass


class ScoreBasedDriftDetector(BatchDriftDetector):
    """Detectors that return a numeric drift score."""
    
    def _produce_result(self, score: float, threshold: float = 0.25, **metadata) -> DriftDetectionResult:
        return DriftDetectionResult(
            drift_score=score,
            drift_detected=score > threshold,
            metadata={"threshold": threshold, **metadata}
        )


class PointwiseDriftDetector(BatchDriftDetector):
    """Detectors that return drift locations in the dataset."""

    def _produce_result(self, drift_points: List[int], **metadata) -> DriftDetectionResult:
        return DriftDetectionResult(
            drift_indices=drift_points,
            drift_detected=bool(drift_points),
            metadata=metadata
        )


class StreamDriftDetector(DriftDetector):
    """Detectors for streaming data, returning drift points over time."""

    def _produce_result(self, drift_points: List[int], **metadata) -> DriftDetectionResult:
        return DriftDetectionResult(
            drift_indices=drift_points,
            drift_detected=bool(drift_points),
            metadata=metadata
        )


class MultivariateDriftDetector:
    """Mixin to mark a detector as multivariate-compatible."""
    
    @property
    def is_multivariate(self) -> bool:
        return True
