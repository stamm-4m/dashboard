# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 15:34:43 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr

"""

# Placeholder implementations for multivariate drift detection methods: PCA-CD and KDQ-tree

import numpy as np


def pca_cd_drift(reference_data: np.ndarray, test_data: np.ndarray, **kwargs) -> dict:
    """
    Placeholder for PCA-based change detection (PCA-CD).

    Returns:
        dict: Dummy result for testing structure
    """
    return {
        "status": "PCA-CD not yet implemented",
        "input_shape_ref": reference_data.shape,
        "input_shape_test": test_data.shape
    }


def kdq_tree_drift(reference_data: np.ndarray, test_data: np.ndarray, **kwargs) -> dict:
    """
    Placeholder for KDQ-tree based detection.

    Returns:
        dict: Dummy result for testing structure
    """
    return {
        "status": "KDQ-tree not yet implemented",
        "input_shape_ref": reference_data.shape,
        "input_shape_test": test_data.shape
    }
