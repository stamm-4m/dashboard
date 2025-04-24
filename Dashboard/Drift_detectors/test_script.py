# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 15:56:02 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr


"""


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
