# -*- coding: utf-8 -*-
"""
Created on Thu Mar 20 09:59:21 2025

@author: David Camilo Corrales
@email: David-Camilo.Corrales-Munoz@inrae.fr

@author: Brett Metcalfe
@email: brett_metcalfe@outlook.com


"""
import sys
import datetime
import numpy as np
#import pandas as pd


class calculate_drift:
    """ CLASS: calculate_drift

        Calculate the model data drift 

        REQUIREMENTS:
            numpy
            datetime
            sys

    """

    def __init__(self):
        """ FUNC: initialise class

            INPUT:
                None
            
            OUTPUT:
                None

        """
        #------------------------------
        # Constants
        self.epsilon = 1e-8

        # User defined variables
        self.bins = None
        self.expected_data = None
        self.actual_data = None

        # Programme computed variables
        self.bin_edges = None
        self.expected_counts = None
        self.actual_counts = None
        self.expected_probs + None
        self.actual_probs = None

        #------------------------------
        # Programme computed variables - drift metrics
        self.psi = None

        #------------------------------
        # Simple metadata - for simplicity just append str to a list
        self.metadata_date_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.metadata = []
        self.metadata.append('calculate_drift: Calculate drift metric')
        self.metadata.append('calculate_drift timestamp: ' + self.metadata_date_time)
        self.metadata.append('calculate_drift requirements: ')
        self.metadata.append('\t numpy version: \t' + str(np.__version__))
        self.metadata.append('\t sys (python) version: \t' + str(sys.version_info))
        self.metadata.append('\t datetime (python) version: \t' + str(sys.version_info))
        self.metadata.append('\n\n')


    def add_expected_data(self, expected_data):
        """ FUNC: Add expected data

            INPUT:
                expected_data = the expected data
            
            OUTPUT:
                None, flattens expected_data
                      modifies self.expected_data
                      add to self.metadata 

        """
        self.expected_data = np.array(expected_data).flatten()

        self.metadata.append('add_expected_data: Flattened expected_data using np.array and np.flatten')
        self.metadata.append('add_expected_data: Set self.expected_data to values of expected_data')


    def add_actual_data(self, actual_data):
        """ FUNC: Add actual data

            INPUT:
                actual_data = the actual, observed, data
            
            OUTPUT:
                None, flattens actual_data
                      modifies self.actual_data 
                      add to self.metadata

        """
        self.actual_data = np.array(actual_data).flatten()

        self.metadata.append('add_actual_data: Flattened actual_data using np.array and np.flatten')
        self.metadata.append('add_actual_data: Set self.actual_data to values of actual_data')

    
    def set_bin_number(self, bins = 10):
        """ FUNC: Set number of histogram bins

            INPUT:
                bins = number of bins, default is 10
            
            OUTPUT:
                None, modifies self.bins 
                      add to self.metadata

        """
        self.bins = bins
        self.metadata.append('set_bin_number: Set self.bins to ' + str(bins))

    
    def compute_bin_edges(self):
        """ FUNC: Compute a histogram bins

            INPUT:
                None
            
            OUTPUT:
                None, modifies self.bin_edges 
                      add to self.metadata


        """
        min_value = min(np.min(expected_data), np.min(actual_data))
        max_value = max(np.max(expected_data), np.max(actual_data))

        self.bin_edges = np.linspace(min_value,max_value, self.bins + 1)
        self.metadata.append('compute_bin_edges: Set self.bin_edges for ' + str(self.bins + 1) + ' bins (i.e., self.bins + 1)')


    def compute_probability_dist(self):
        """ FUNC: compute probability distribution 

            INPUT: 
                None

            OUTPUT:
                None, modifies self.expected_counts
                      modifies self.actual_counts
                      modifies self.expected_probs
                      modifies self.actual_probs
                      add to self.metadata

        """
        #------------------------------
        # Get the counts in each bin for expected and actual data
        self.expected_counts, _ = np.histogram(self.expected_data, bins=self.bin_edges)
        self.actual_counts, _ = np.histogram(self.actual_data, bins=self.bin_edges)

        self.metadata.append('compute_probability_dist: Set self.expected_counts using np.histogram and self.bin_edges ')
        self.metadata.append('compute_probability_dist: Set self.actual_counts using np.histogram and self.bin_edges' )


        #------------------------------
        # Convert counts to proportions (probability distribution)
        expected_probs = self.expected_counts / sum(self.expected_counts)
        actual_probs = self.actual_counts / sum(self.actual_counts)
        self.metadata.append('compute_probability_dist: Convert expected counts to proportions ')
        self.metadata.append('compute_probability_dist: Convert actual counts to proportions ')


        #------------------------------
        # To avoid division by zero or log(0), add a small value to avoid NaN
        expected_probs = np.clip(expected_probs, self.epsilon, 1)
        actual_probs = np.clip(actual_probs, self.epsilon, 1)
        self.metadata.append('compute_probability_dist: Add self.epsilon (' + str(self.epsilon) + ') to expected proportions (expected_probs) using np.clip')
        self.metadata.append('compute_probability_dist: Add self.epsilon (' + str(self.epsilon) + ') to actual proportions (actual_probs) using np.clip')


        #------------------------------
        # Set output
        self.expected_probs = expected_probs
        self.actual_probs   = actual_probs
        self.metadata.append('compute_probability_dist: Set self.expected_probs')
        self.metadata.append('compute_probability_dist: Set self.actual_probs')


    #---------------------------------
    # METADATA FUNCTIONS
    def export_metadata(self, export_name = '_METADATA.txt', export_dir = None):
        """ EXPORT: export the metadata file

            INPUT:
                export_name = export filename, default is _METADATA.txt

            OUTPUT:
                None, exports metadata as <datetime now><export_name> 

        """
        export_name = self.metadata_date_time + export_name

        if export_dir is not None:
            export_name = os.path.join(export_dir, export_name)

        self.metadata.append('export_metadata: Export metadata to ' + str(export_name))

        with open(export_name, 'w') as f:
            for line in self.metadata:
                f.write("%s\n" % line)


    #---------------------------------
    # DRIFT DETECTION FUNCTIONS - PSI
    def compute_psi(self):
        """ FUNC: compute the Population Stability Index (PSI)

            INPUT: 
                None

            OUTPUT:
                None, modifies self.psi

        """
        # Calculate PSI for each bin
        self.psi = np.sum((self.actual_probs - self.expected_probs) * np.log(self.actual_probs / self.expected_probs))

        self.metadata.append('compute_psi: Calculate PSI for each bin and set self.psi')


    def calculate_psi(self, expected_data, actual_data, bins=10, output_metadata = False):
        """ WRAPPER: Set values and calculate the Population Stability Index (PSI).

            INPUT:
                expected_data   = Data from the reference (or training) population.
                actual_data     = Data from the current (or production) population.
                bins            = Number of bins to categorize data for PSI calculation, default is 10
                output_metadata = Whether to return the metadata alongside the metric or not, default is False

            OUTPUT:
                psi             = Population Stability Index value.

        """
        self.metadata.append('')
        self.metadata.append('calculate_psi:  ')
        self.metadata.append('DRIFT DETECTION METRIC: Population Stability Index (PSI)')
        self.metadata.append('')
        self.add_expected_data(expected_data)
        self.add_actual_data(actual_data)
        self.set_bin_number(bins)
        self.compute_bin_edges()
        self.compute_probability_dist()
        self.compute_psi()
        
        if output_metadata:
            
            self.metadata.append('calculate_psi: return self.psi and self.metadata ')
            return self.psi, self.metadata

        else:

            self.metadata.append('calculate_psi: return self.psi')
            return self.psi

    
    #---------------------------------
    # DRIFT DETECTION FUNCTIONS - ADWIN




def calculate_psi(expected_data, actual_data, bins=10):
    """
    Calculate the Population Stability Index (PSI).

    Parameters:
    - expected_data: Data from the reference (or training) population.
    - actual_data: Data from the current (or production) population.
    - bins: Number of bins to categorize data for PSI calculation.

    Returns:
    - psi: Population Stability Index value.
    """
    # Ensure the data is in the same shape (1D arrays)
    expected_data = np.array(expected_data).flatten()
    actual_data = np.array(actual_data).flatten()

    # Create bins for the data
    bin_edges = np.linspace(min(np.min(expected_data), np.min(actual_data)),
                            max(np.max(expected_data), np.max(actual_data)),
                            bins + 1)

    # Get the counts in each bin for expected and actual data
    expected_counts, _ = np.histogram(expected_data, bins=bin_edges)
    actual_counts, _ = np.histogram(actual_data, bins=bin_edges)

    # Convert counts to proportions (probability distribution)
    expected_probs = expected_counts / sum(expected_counts)
    actual_probs = actual_counts / sum(actual_counts)

    # To avoid division by zero or log(0), add a small value to avoid NaN
    epsilon = 1e-8
    expected_probs = np.clip(expected_probs, epsilon, 1)
    actual_probs = np.clip(actual_probs, epsilon, 1)

    # Calculate PSI for each bin
    psi = np.sum((actual_probs - expected_probs) * np.log(actual_probs / expected_probs))

    return psi

