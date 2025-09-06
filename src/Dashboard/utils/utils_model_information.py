import yaml
import os
import pandas as pd
import logging
from Dashboard.config import BASE_URL_API
from Dashboard.utils.utils_apiclient import ApiClient





# Class to manage information from ML model files
class ModelInformation:

    def __init__(self):
        # Create instance for Client
        self.api_client = ApiClient(BASE_URL_API)
        self.configurations = []
        self.configurations_monitoring = []
        self.variable_categories = {
                "sensor": [
                    "air_head_pressure", "dissolved_oxygen_concentration", "pH", 
                    "temperature", "generated_heat", "CO2_percent_in_off_gas",
                    "oxygen_uptake_rate", "oxygen_in_percent_in_off_gas",
                    "carbon_evolution_rate"
                ],
                "actuator": [
                    "aeration_rate", "agitator", "sugar_feed_rate", "acid_flow_rate", "base_flow_rate", 
                    "heating/cooling_water_flow_rate", "heating_water_flow_rate", "water_for_injection/dilution",
                    "dumped_broth_flow", "substrate_concentration", "PAA_flow", "oil_flow", "ammonia_shots"
                ],
                "computed_variable": [
                    "vessel_volume", "vessel_weight"
                ],
                "soft_sensor": [
                    "penicillin_concentration"
                ],
                "offline_measurement": [
                    "PAA_concentration", "NH3_concentration", "offline_penicillin_concentration",
                    "offline_biomass_concentration", "viscosity"
                ]
            }

    def load_data_model(self, model_name):
        """Loads  and adds it to the configurations list."""
        try:
            response = self.api_client.get("metadata/"+model_name)
            self.configurations.append(response)
        except Exception as e:
            print(f" Error load model data: {e}")

    def load_all_models(self):
        """Loads all models"""
        try:
            response = self.api_client.get("list_models")
            for modelo in response['available_soft_sensors']:
                self.load_data_model(modelo['name'])
        except Exception as e:
            print(f" Error load all models: {e}")

        

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

    # Function to get model file information as a DataFrame
    def get_models_dataframe(self):
        """Returns a DataFrame with information about the loaded models."""
        data = []
        for config in self.configurations:
            model_config = config.get('ml_model_configuration', {})

            model_ident = model_config.get('model_identification', {})
            model_desc = model_config.get('model_description', {})
            model_pack = model_desc.get('packages', [])  # Asegura que sea una lista
            model_train = model_config.get('training_information', {})
            model_inputs = model_config.get('inputs', {}).get('features', [])
            model_outputs = model_config.get('outputs', {}).get('predictions', [])

            row = {
                # Model Identification
                "Name": model_ident.get('name', 'N/A'),
                "Version": model_ident.get('version', 'N/A'),
                "UUID": model_ident.get('UUID', 'N/A'),
                "Author": model_ident.get('author', 'N/A'),
                "Doi": model_ident.get('doi', 'N/A'),
                "Creation date": model_ident.get('creation_date', 'N/A'),

                # Model Description
                "Learner": model_desc.get('learner', 'N/A'),
                "Model type": model_desc.get('model_type', 'N/A'),
                "Model Name": model_desc.get('model_name', 'N/A'),
                "Description": model_desc.get('description', 'N/A'),
                "Language": model_desc.get('language', 'N/A'),
                "Model File": model_desc.get('config_files', {}).get('model_file', 'N/A'),

                # Model Packages
                "Packages": ', '.join(
                    [f"{pkg.get('package', 'Unknown')} - {pkg.get('version', 'Unknown')}" for pkg in model_pack]
                ) if isinstance(model_pack, list) else "No packages available",

                # Model Description Interval
                "Interval value": model_desc.get('input_time_interval', {}).get('time_interval', {}).get('value', 'N/A'),
                "Interval unit": model_desc.get('input_time_interval', {}).get('time_interval', {}).get('unit', 'N/A'),
                "Interval description": model_desc.get('input_time_interval', {}).get('description', 'N/A'),
                "Aggregation method": model_desc.get('input_time_interval', {}).get('aggregation', {}).get('method', 'N/A'),
                "Aggregation description": model_desc.get('input_time_interval', {}).get('aggregation', {}).get('description', 'N/A'),

                # Model Training
                "Number of instances": model_train.get('number_of_instances', 'N/A'),
                "Number of trees": model_train.get('hyperparameters', {}).get('number_of_trees', 'N/A'),
                "Max tree depth": model_train.get('hyperparameters', {}).get('max_tree_depth', 'N/A'),
                "Validation": model_train.get('validation', 'N/A'),
                "Experiments ID": model_train.get('experiments_ID', 'N/A'),

                # Model Inputs/Outputs
                "Number of Inputs": len(model_inputs),
                "Input Names": ', '.join([input.get('name', 'Unknown') for input in model_inputs]),
                "Number of Outputs": len(model_outputs),
                "Output Names": ', '.join([output.get('name', 'Unknown') for output in model_outputs]),
            }

            data.append(row)

        return pd.DataFrame(data)
    # Function to load inputs from configuration
    def load_inputs_from_configuration(self, model_name):
        config = self.get_configuration_by_model_name(model_name)
        #model_config = config.get('ml_model_configuration', {})
        inputs = config['inputs'].get("features", [])
        # Create options for the Dropdown
        return [{"label": feature['name'], "value": feature['name']} for feature in inputs]

    def load_yaml_file_monitoring(self, filepath):
        """Loads a YAML file and adds it to the configurations list."""
        try:
            with open(filepath, 'r', encoding="utf-8") as file:
                config = yaml.safe_load(file)
                self.configurations_monitoring.append(config)
        except FileNotFoundError:
            print(f"File not found: {filepath}")
        except yaml.YAMLError as exc:
            print(f"Error reading the YAML file: {exc}")

    def load_multiple_yaml_files_monitoring(self, folder_path):
        """Loads all YAML files from a folder."""
        for filename in os.listdir(folder_path):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(folder_path, filename)
                self.load_yaml_file_monitoring(filepath)
    
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
                    print("Model not found in configuration")
                    return []  # Or return an empty list []
            except Exception as e:
                print(f"Error processing get category: {e}")
                return [] 
                
    
    def get_feature_categories(self, config):
        categories = set()
        for feature in config["inputs"].get('features', []):
            feature_name = feature['name']
            for category, variables in self.variable_categories.items():
                if feature_name in variables:
                    categories.add(category)
        return list(categories)
    
    def get_names_by_category(self, category, model_name):
        for config in self.configurations:
            try:
                if category:
                    # Navigate through the configuration structure to find the model
                    model_config = config.get('model_description', {})
                    if model_config.get('model_name') == model_name:
                        # Get list name in  variable_categories by category selected
                        valid_names = self.variable_categories.get(category, [])
                        print("valid_names: ",valid_names)
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
        """Get projetc details information"""
        try:
            response = self.api_client.get("project_info/")
            return response
        except Exception as e:
            print(f" Error get project details data: {e}")