from functools import lru_cache

import yaml
import os
import pandas as pd
import logging
from Dashboard.config import BASE_URL_API,PROJECT_ID
from Dashboard.utils.utils_apiclient import ApiClient

logger = logging.getLogger(__name__)

# Class to manage information from ML model files
class ModelInformation:

    def __init__(self, project_id=None):
        # Create instance for Client
        self.api_client = ApiClient(BASE_URL_API)
        self.base_project_id = project_id
        self.configurations = []
        self.configurations_monitoring = []
        
    def load_data_model(self, model_id):
        """Loads  and adds it to the configurations list."""
        try:
            response = self.api_client.get(f"{self.base_project_id}/metadata/"+model_id)
            self.configurations.append(response)
        except Exception as e:
            logger.error(f" Error load model data: {e}")

    def load_all_models(self):
        """Loads all models"""
        try:
            response = self.api_client.get(f"{self.base_project_id}/list_models")
            for modelo in response:
                #logger.debug(f"modelo:{modelo}")
                if modelo["metadata"]["status"] == "online":
                    self.load_data_model(modelo['model_ID'])
        except Exception as e:
            logger.error(f" Error load all models: {e}")

        

    def get_configurations(self):
        """Returns all loaded configurations."""
        return self.configurations

    def get_configuration_by_filename(self, filename):
        """Returns a specific configuration based on the file name."""
        for config_entry in self.configurations:
            if config_entry['model_description']['config_files']['model_file'] == filename:
                return config_entry
        return None


    def get_configuration_by_model_name(self, model_name):
        """Returns a specific configuration based on the model name."""
        for config in self.configurations:
            if config['model_description']['model_name'] == model_name:
                return config
        return None
    
    def get_configuration_by_model_id(self, model_id):
        """Returns a specific configuration based on the model id."""
        for config in self.configurations:
            if config['model_identification']['ID'] == model_id:
                return config
        return None
    
    def get_configuration_by_model_name_language(self, model_name):
        """Returns a specific configuration based on the model name and language."""
        for config in self.configurations:
            if config['model_description']['model_name'] == model_name:
                return config
        return None

    # Function to list options for a dropdown
    def get_model_options(self):
        """Returns a list of model options for a Dash dropdown component."""
        return [
            {
                'label': a_config['ml_model_configuration']['model_description']['model_name'] + " - " + a_config['ml_model_configuration']['model_description']['config_files']['model_file'],
                'value': a_config['ml_model_configuration']['model_description']['config_files']['model_file']
            }
            for a_config in self.configurations
        ]

    def get_languages_for_model(self,model_name):
        """
        Searches loaded configurations and returns the languages associated with a specific model.

        Parameters:
            model_name (str): Name of the model to search for.
            configurations (list): List of loaded YAML configurations.

        Returns:
            list: List of unique languages associated with the model.
        """
        languages = set()  # Use a set to avoid duplicates

        # Iterate through all configurations
        for config in self.configurations:
            try:
                # Navigate through the configuration structure to find the model
                model_config = config.get('ml_model_configuration', {}).get('model_description', {})
                if model_config.get('model_name') == model_name:
                    # Add the language to the set
                    language = model_config.get('language')
                    print("language:",language["name"])
                    if language:
                        languages.add(language["name"])
            except Exception as e:
                print(f"Error processing configuration: {e}")

        return sorted(languages)  # Return the list of unique languages sorted



    # Function to list unique options for model name
    def get_model_name_options(self):
        logger.debug("Generating model name options for dropdown")
        """Returns a list of unique model name options for a Dash dropdown component."""
        # Use a set to collect unique model names
        unique_names = {
            a_config['model_description']['model_name']
            for a_config in self.configurations
        }
        
        # Return a list of dictionaries with label and value
        return [{'label': name, 'value': name} for name in sorted(unique_names)]
    
    def get_model_id_options(self):
        """Returns a list of unique model options for a Dash dropdown component.

        Each option includes label, value, name (the model ID), and id (the model UUID).
        """
        options = []

        for a_config in self.configurations:
            model_info = a_config.get("model_identification", {})
            model_id = model_info.get("ID")
            model_info = a_config.get("model_description", {})
            model_name = model_info.get("model_name")

            # Skip invalid entries
            if not model_id or not model_name:
                continue

            options.append({
                "label": model_name,   # Visible in the dropdown
                "value": model_id,   # Used as value in callbacks
            })

        #logger.debug(f"Model options generated: {options}")
        return options

        # Function to load inputs from configuration
    def load_inputs_from_configuration(self, model_name):
        """
        Load the list of input features from the model configuration.

        Parameters
        ----------
        model_name : str
            Name of the model to retrieve configuration for.

        Returns
        -------
        list[dict]
            A list of dictionaries representing dropdown options. Each entry
            includes a 'label' and a 'value' corresponding to a feature name.
        """
        config = self.get_configuration_by_model_name(model_name) or {}

        # Safely extract features without raising errors
        inputs_section = config.get("inputs", {})
        features = inputs_section.get("features", [])

        # Build dropdown options
        return [{"label": f["name"], "value": f["name"]} for f in features]

    # Gets all unique categories from the 'type' field within inputs.
    def get_unique_types_models(self, model_name):
        for config in self.configurations:
            try:
                if model_name:
                    # Navigate through the configuration structure to find the model
                    model_config = config.get('model_description', {})
                    if model_config.get('model_name') == model_name:
                        #print("config: ",config)
                        return self.get_feature_categories(config)
                else:

                    logger.info("Model not found in configuration")
                    return []  # Or return an empty list []
            except Exception as e:
                print(f"Error processing get category: {e}")
                return [] 
                
    
    def get_feature_categories(self, config):
        """
        Extract unique feature categories from the configuration.

        This method iterates over the list of input features in the configuration
        dictionary and collects all unique feature categories based on their "type".
        Using a set ensures that no duplicate categories are returned.

        Parameters
        ----------
        config : dict
            The configuration dictionary containing input feature definitions
            under the key "inputs" → "features".

        Returns
        -------
        list
            A list of unique feature category names found in the configuration.

        Examples
        --------
        >>> config = {
        ...     "inputs": {
        ...         "features": [
        ...             {"name": "temperature", "type": "sensor"},
        ...             {"name": "pressure", "type": "sensor"},
        ...             {"name": "batch_id", "type": "metadata"}
        ...         ]
        ...     }
        ... }
        >>> obj.get_feature_categories(config)
        ['sensor', 'metadata']
        """
        categories = set()
        for feature in config.get("inputs", {}).get("features", []):
            feature_category = feature.get("type")
            if feature_category:
                categories.add(feature_category)
        return list(categories)

    def get_names_by_category(self, category, model_name):
        for config in self.configurations:
            try:
                if category:
                    # Navigate through the configuration structure to find the model
                    model_config = config.get('model_description', {})
                    if model_config.get('model_name') == model_name:
                        # Get list features for model selected
                        filtered_inputs = [
                                {"label": feature['name'], "value": feature['name']}
                        for feature in config["inputs"].get('features', [])
                        if feature["type"] in category
                        ]
                        return filtered_inputs
                else:
                    print("Model not found name input")
                    return []  # Or return an empty list []
            except Exception as e:
                print(f"Error processing get name input: {e}")

    
    def project_details(self, project_id):
        """
        Retrieve detailed information about a specific project.

        This method sends a GET request to the API endpoint `"{project_id}/project_info/"`
        using the provided project identifier. It returns the project details
        if the request is successful, otherwise logs an error message.

        Returns
        -------
        dict or None
            The project details as a dictionary if the request is successful.
            Returns None if an error occurs during the API request.

        Raises
        ------
        Exception
            If an unexpected error occurs during the API request.
        """
        logger.debug(f"Fetching project details for project_id: {project_id}")
        try:
            response = self.api_client.get(f"{project_id}/project_info/")
            return response
        except Exception as e:
            logger.error(f"Error getting project details data: {e}")
            return None
        
    
def list_projects():
        """
        Retrieve a list of project names from the API.

        This method sends a GET request to the API endpoint list_projects/
        to fetch a list of projects. It extracts and returns the project names
        from the response if the request is successful, otherwise logs an error message.

        Returns
        -------
        list or None
            A list of project names and project_ID if the request is successful.
            Returns None if an error occurs during the API request.

        Raises
        ------
        Exception
            If an unexpected error occurs during the API request.
        """
        try:
            api_client = ApiClient(BASE_URL_API)
            response = api_client.get("list_projects/")
            project_names = [{"name": project['name'], "id": project['project_ID']} for project in response]
            return project_names
        except Exception as e:
            logger.error(f"Error getting project names: {e}")
            return None
        
@lru_cache(maxsize=32)
def get_model_information(project_id):
    return ModelInformation(project_id)