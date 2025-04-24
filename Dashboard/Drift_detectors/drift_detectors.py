# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 15:36:02 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr


"""

# Central dispatcher to route drift detection requests to appropriate univariate or multivariate functions.

# drift_detectors.py

from typing import Union, Optional
import numpy as np
from metadata_utils import get_algorithm_function

def univariate_drift(method: str,
                     reference_data: Optional[np.ndarray],
                     test_data: np.ndarray,
                     **kwargs) -> Union[float, dict]:
    method = method.upper()
    algo_fn = get_algorithm_function(method)

    if method == "PSI" and reference_data is None:
        raise ValueError("reference_data is required for PSI.")
    
    if method == "PSI":
        return algo_fn(reference_data, test_data, **kwargs)
    else:
        return algo_fn(test_data, **kwargs)


def multivariate_drift(method: str,
                       reference_data: np.ndarray,
                       test_data: np.ndarray,
                       **kwargs) -> dict:
    method = method.upper()
    algo_fn = get_algorithm_function(method)
    return algo_fn(reference_data, test_data, **kwargs)
