from typing import List
from typing import Optional

class DriftDetectionResult:
    def __init__(
        self,
        drift_indices: Optional[List[int]] = None,
        drift_score: Optional[float] = None,
        drift_detected: Optional[bool] = None,
        metadata: Optional[dict] = None,
    ):
        self.drift_indices = drift_indices
        self.drift_score = drift_score
        self.drift_detected = drift_detected
        self.metadata = metadata or {}

        # Optional auto-detection if not provided
        if self.drift_detected is None:
            if self.drift_score is not None:
                self.drift_detected = self.drift_score > 0.25
            elif self.drift_indices is not None:
                self.drift_detected = len(self.drift_indices) > 0
            else:
                self.drift_detected = False

        self.num_drifts = (
            len(self.drift_indices) if self.drift_indices is not None else None
        )

    def has_drift(self):
        if self.drift_score >= 1.0:
            return "drift", self.drift_score
        elif self.drift_score >= 0.5:
            return "moderate", self.drift_score
        else:
            return "stable", self.drift_score