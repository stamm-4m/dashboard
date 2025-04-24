# -*- coding: utf-8 -*-
"""
Created on Thu Apr 10 15:48:14 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr


"""

from setuptools import setup, find_packages

setup(
    name='drift_detection',
    version='0.1',
    description='Modular data drift detection for univariate and multivariate time series',
    author='David Camilo Corrales & brett_metcalfe@outlook.com',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'river'  # Optional, only needed for ADWIN
    ],
)
