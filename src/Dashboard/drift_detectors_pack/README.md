# Drift Detection Framework
A modular and extensible Python package for detecting data drift in both univariate and multivariate settings.
Supports statistical and model-based approaches with a unified class-based architecture.

## Overview
This framework provides:
* A common `DriftDetector` interface with a standard `calculate()` method
* Multiple built-in detectors (`PSI`, `ADWIN`, `PCA-CD`, etc.)
* Support for both batch and streaming data drift detection
* A flexible system of intermediate abstract base classes to categorize detectors by type
* Structured, standardized outputs via `DriftDetectionResult`
* Detector metadata in a YAML registry with utilities for documentation

## Architecture
All detectors inherit from a base class and implement a standardized interface:
```
DriftDetector (ABC)
├── BatchDriftDetector
│   ├── ScoreBasedDriftDetector
│   └── PointwiseDriftDetector
├── StreamDriftDetector
└── MultivariateDriftDetector (Mixin)
```
### Key Interface
All concrete detectors implement:
```python
def calculate(self, ...**kwargs) -> DriftDetectionResult
```

### Result Format
```python
DriftDetectionResult(
    drift_detected: bool,
    drift_indices: Optional[List[int]] = None,
    psi_value: Optional[float] = None,
    metadata: Optional[dict] = None
)
```

### Examples
```python
from univariate.psi import PSI
from univariate.adwim import Adwin
from multivariate.mmd import MMDDetector
  
ref_data = np.random.normal(0, 1, 1000)
test_data = np.random.normal(0.5, 1, 1000)
stream_data = np.concatenate([np.random.normal(0, 1, 500), np.random.normal(2, 1, 500)])

# PSI (batch, univariate)
psi = PSI()
psi_result = psi.calculate(ref_data, test_data)
print("PSI drift detected:", psi_result.drift_detected, "| Value:", psi_result.psi_value)

# ADWIN (stream, univariate)
adwin = Adwin()
adwin_result = adwin.calculate(stream_data, delta=0.002)
print("ADWIN drift points:", adwin_result.drift_indices)

# MMD (batch, multivariate)
ref_matrix = np.random.rand(100, 5)
test_matrix = np.random.rand(100, 5)
mmd = MMDDetector()
mmd_result = mmd.calculate(ref_matrix, test_matrix)
print("MMD score:", mmd_result.psi_value)
```

### Accessing Algorithm Metadata
Each detector automatically loads metadata from algorithm_metadata.yaml.
```python
from univariate.psi import PSI

psi = PSI()
info = psi.get_algorithm_info()

print("Name:", info["name"])
print("Description:", info["description"])
print("Thresholds:", info["thresholds"])
```

To generate a markdown summary table:

```python
from drift_detectors.utility.metadata import generate_markdown_table

print(generate_markdown_table())

```

## Adding New Detectors 
To implement a new detector:
* Inherit from the appropriate base class (ScoreBasedDriftDetector StreamDriftDetector, etc.)
* Implement the calculate() method
* Optionally define _produce_result(score, **kwargs) if not using default
* Add metadata to algorithm_metadata.yaml