# Drift Detection Module

A modular Python package for univariate and multivariate data drift detection.

## 📁 Structure

```
drift_detection/
│
├── __init__.py              # For easy importing
├── drift_detector.py        # Generic dispatcher for univariate/multivariate
├── univariate.py            # PSI, ADWIN, and similar 1D methods
└── multivariate.py          # PCA-CD, KDQ-tree and similar multivariate methods
```

## ✅ Features

- **Univariate Drift**
  - PSI (Population Stability Index)
  - ADWIN (via `river`)

- **Multivariate Drift**
  - PCA-CD (placeholder)
  - KDQ-tree (placeholder)

## 🚀 Installation

```bash
pip install river
```

## 🧪 Usage

```python
# sys.path.append("C:/Users/corrales/Documents/STAMM/")
import numpy as np
from drift_detectors import univariate_drift, multivariate_drift

# Create synthetic data
np.random.seed(42)
ref_data = np.random.normal(0, 1, 1000)
test_data = np.random.normal(0.5, 1, 1000)
stream_data = np.concatenate([np.random.normal(0, 1, 500), np.random.normal(2, 1, 500)])

# PSI
psi = univariate_drift("PSI", ref_data, test_data)
print(f"PSI: {psi:.4f}")

# ADWIN
try:
    adwin = univariate_drift("ADWIN", None, stream_data, delta=0.002)
    print("ADWIN result:", adwin)
except ImportError as e:
    print(e)

# Multivariate placeholder
ref_matrix = np.random.rand(100, 5)
test_matrix = np.random.rand(100, 5)
pca_result = multivariate_drift("PCA-CD", ref_matrix, test_matrix)
print("PCA-CD placeholder:", pca_result)

```
## 📘 Example: Fetch Metadata

```python
from metadata_utils import get_algorithm_info

info = get_algorithm_info("ADWIN")
print("Name:", info["name"])
print("Description:", info["description"])
print("Method:", info["method"])
print("Thresolds:", info["thresholds"])
print("Configuration:", info["configuration"])
print("Implementation notes:", info["implementation_notes"])
print("Parameters:", info["parameters"])
```


## 🔧 TODO

- Implement PCA-CD and KDQ-tree logic
- Add statistical tests
- Improve visualisation and logging
