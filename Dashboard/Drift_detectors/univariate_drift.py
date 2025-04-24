# -*- coding: utf-8 -*-
"""
Created on Thu Mar 20 09:59:21 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr

"""
# Module for univariate drift detection methods: PSI and ADWIN

import numpy as np
from typing import Union


def psi_drift(reference_data: np.ndarray, test_data: np.ndarray, bins: int = 10, epsilon: float = 1e-8) -> float:
    """
    Calculate the Population Stability Index (PSI).

    Parameters:
        reference_data (np.ndarray): Historical or training data (1D).
        test_data (np.ndarray): Current or new data (1D).
        bins (int): Number of histogram bins.
        epsilon (float): Small value to avoid log(0).

    Returns:
        float: PSI value
    """
    reference_data = np.asarray(reference_data).flatten()
    test_data = np.asarray(test_data).flatten()

    bin_edges = np.linspace(min(reference_data.min(), test_data.min()),
                            max(reference_data.max(), test_data.max()),
                            bins + 1)

    ref_counts, _ = np.histogram(reference_data, bins=bin_edges)
    test_counts, _ = np.histogram(test_data, bins=bin_edges)

    ref_probs = np.clip(ref_counts / ref_counts.sum(), epsilon, 1)
    test_probs = np.clip(test_counts / test_counts.sum(), epsilon, 1)

    psi = np.sum((test_probs - ref_probs) * np.log(test_probs / ref_probs))
    return psi


def adwin_drift(test_data: np.ndarray, delta: float = 0.002) -> dict:
    """
    Run ADWIN drift detection on a univariate sequence.

    Parameters:
        test_data (np.ndarray): Streaming sequence (1D).
        delta (float): Confidence value, smaller means stricter.

    Returns:
        dict: Drift detection result including indices and count.
    """
    try:
        from river.drift import ADWIN
        HAS_RIVER = True
    except ImportError:
        raise ImportError("Please install the 'river' library for ADWIN support: pip install river")

    detector = ADWIN(delta=delta)
    drift_points = []

    for i, value in enumerate(test_data):
        detector.update(value)
        if detector.drift_detected:
            drift_points.append(i)

    return {
        "drift_detected": len(drift_points) > 0,
        "drift_indices": drift_points,
        "num_drifts": len(drift_points)
    }
