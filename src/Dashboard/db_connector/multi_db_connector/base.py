# -*- coding: utf-8 -*-
"""
Created on Wed May 14 10:04:33 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr

"""

from abc import ABC, abstractmethod

class BaseDBConnector(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def query(self, query_str):
        pass

    def close(self):
        pass