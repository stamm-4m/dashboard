import yaml
import os
import pandas as pd
import logging
from Dashboard.config import BASE_URL_API,PROJECT_ID
from Dashboard.utils.utils_apiclient import ApiClient

logger = logging.getLogger(__name__)

# Class to manage information from ML model files
class ModelInformation:

    def __init__(self):
        # Create instance for Client
        self.api_client = ApiClient(BASE_URL_API)
        self.base_project_id = PROJECT_ID
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
        """Returns a list of unique model name options for a Dash dropdown component."""
        # Use a set to collect unique model names
        unique_names = {
            a_config['model_description']['model_name']
            for a_config in self.configurations
        }
        
        # Return a list of dictionaries with label and value
        return [{'label': name, 'value': name} for name in sorted(unique_names)]

    # Function to load inputs from configuration
    def load_inputs_from_configuration(self, model_name):
        config = self.get_configuration_by_model_name(model_name)
        #model_config = config.get('ml_model_configuration', {})
        inputs = config['inputs'].get("features", [])
        # Create options for the Dropdown
        return [{"label": feature['name'], "value": feature['name']} for feature in inputs]

    """def load_yaml_file_monitoring(self, filepath):
        "Loads a YAML file and adds it to the configurations list."
        try:
            with open(filepath, 'r', encoding="utf-8") as file:
                config = yaml.safe_load(file)
                self.configurations_monitoring.append(config)
        except FileNotFoundError:
            print(f"File not found: {filepath}")
        except yaml.YAMLError as exc:
            print(f"Error reading the YAML file: {exc}")"""

    """def load_multiple_yaml_files_monitoring(self, folder_path):
        "Loads all YAML files from a folder."
        for filename in os.listdir(folder_path):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(folder_path, filename)
                self.load_yaml_file_monitoring(filepath)"""
    
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

    
    def project_details(self):
        """
        Retrieve detailed information about a specific project.

        This method sends a GET request to the API endpoint `"{self.base_project_id}/project_info/"`
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
        try:
            response = self.api_client.get(f"{self.base_project_id}/project_info/")
            return response
        except Exception as e:
            logger.error(f"Error getting project details data: {e}")
            return None
