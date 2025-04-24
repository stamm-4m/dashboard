import yaml
import os
import pandas as pd
import logging


# Class to manage information from ML model files
class ModelConfigLoader:
    def __init__(self):
        self.configurations = []
        self.configurations_monitoring = []
        

    def load_yaml_file(self, filepath):
        """Loads a YAML file and adds it to the configurations list."""
        try:
            with open(filepath, 'r',encoding="utf-8") as file:
                config = yaml.safe_load(file)
                self.configurations.append(config)
        except FileNotFoundError:
            print(f"File not found: {filepath}")
        except yaml.YAMLError as exc:
            print(f"Error reading the YAML file: {exc}")

    def load_multiple_yaml_files(self, folder_path):
        """Loads all YAML files from a folder."""
        for filename in os.listdir(folder_path):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(folder_path, filename)
                self.load_yaml_file(filepath)

    def get_configurations(self):
        """Returns all loaded configurations."""
        return self.configurations

    def get_configuration_by_filename(self, filename):
        """Returns a specific configuration based on the file name."""
        for config_entry in self.configurations:
            if config_entry['ml_model_configuration']['model_description']['config_files']['model_file'] == filename:
                return config_entry
        return None


    def get_configuration_by_model_name(self, model_name):
        """Returns a specific configuration based on the model name."""
        for config in self.configurations:
            if config['ml_model_configuration']['model_description']['model_name'] == model_name:
                return config
        return None
    
    def get_configuration_by_model_name_language(self, model_name):
        """Returns a specific configuration based on the model name and language."""
        for config in self.configurations:
            if config['ml_model_configuration']['model_description']['model_name'] == model_name:
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
            a_config['ml_model_configuration']['model_description']['model_name']
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
    # Function to load inputs from a YAML file
    def load_inputs_from_yaml(self, model_name):
        config = self.get_configuration_by_model_name(model_name)
        model_config = config.get('ml_model_configuration', {})
        
        inputs = model_config.get("inputs", {}).get("features", [])
        # Create options for the Dropdown
        return [{"label": feature["name"], "value": feature["name"]} for feature in inputs]

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

    def get_metrics_score_options(self):
        self.load_multiple_yaml_files_monitoring("../Monitoring/data_drift_detectors")
        metrics = set()  # Use a set to avoid duplicate values

        for config in self.configurations_monitoring:
            try:
                # Extract the detector name from the configuration
                name = config.get('drift_detector', {}).get('acronym', None)

                if name:  # Avoid empty or None values
                    metrics.add(name)
            except Exception as e:
                logging.error(f"Error processing configuration monitoring: {e}")

        # Convert unique values into a list of dictionaries
        return [{"label": metric, "value": metric} for metric in sorted(metrics)]
    
    # Searches for the selected metric in the already loaded YAML files in configurations_monitoring
    def load_metric_descriptions(self, selected_metric):
        # Default values in case the metric is not found
        default_response = {
            "name": "Unknown Metric",
            "thresholds": {"low": "N/A", "moderate": "N/A", "high": "N/A"},
            "configuration": {}
        }

        for config in self.configurations_monitoring:
            try:
                drift_detector = config.get('drift_detector', {})

                if drift_detector.get("acronym") == selected_metric:
                    return {
                        "name": drift_detector.get("name", "Unknown Metric"),
                        "thresholds": drift_detector.get("thresholds", default_response["thresholds"]),
                        "configuration": drift_detector.get("configuration", {})
                    }
            except Exception as e:
                print(f"Error retrieving metric information {selected_metric}: {e}")

        return default_response
    
    # Gets all unique categories from the 'type' field within inputs.
    def get_unique_types_models(self, model_name):
        for config in self.configurations:
            try:
                if model_name:
                    # Navigate through the configuration structure to find the model
                    model_config = config.get('ml_model_configuration', {}).get('model_description', {})
                    if model_config.get('model_name') == model_name:
                        return list(set(feature["type"] for feature in config["ml_model_configuration"]["inputs"]["features"]))
                else:
                    print("Model not found in configuration")
                    return []  # Or return an empty list []
            except Exception as e:
                print(f"Error processing get category: {e}")
    
    def get_names_by_category(self, category, model_name):
        for config in self.configurations:
            try:
                if category:
                    # Navigate through the configuration structure to find the model
                    model_config = config.get('ml_model_configuration', {}).get('model_description', {})
                    if model_config.get('model_name') == model_name:
                        filtered_inputs = [
                            {"label": feature["name"], "value": feature["name"]}
                            for feature in config["ml_model_configuration"]["inputs"]["features"]
                            if feature["type"] == category
                        ]
                        return filtered_inputs
                else:
                    print("Model not found name input")
                    return []  # Or return an empty list []
            except Exception as e:
                print(f"Error processing get name input: {e}")

    def get_performance_estimators_options(self):
        self.load_multiple_yaml_files_monitoring("../Monitoring/performance_estimators")
        estimators = set()

        for config in self.configurations_monitoring:
            try:
                # Extract the list of detectors from the configuration
                drift_detectors = config.get('drift_detector', [])
                
                if isinstance(drift_detectors, list):
                    for detector in drift_detectors:
                        name = detector.get('name')
                        acronym = detector.get('acronym')
                        
                        if name and acronym:  # Ensure both values exist
                            estimators.add((name, acronym))
            except Exception as e:
                logging.error(f"Error processing configuration estimator: {e}")

        # Convert unique values into a list of dictionaries
        return [{"label": acronym, "value": acronym} for name, acronym in sorted(estimators)]
    
    def load_estimator_descriptions(self, selected_estimator):
        # Default values in case the metric is not found
        default_response = {
            "name": "Unknown Metric",
            "method": {},
            "configuration": {},
            "implementation_notes": []
        }

        for config in self.configurations_monitoring:
            try:
                drift_detectors = config.get('drift_detector', [])
                
                if isinstance(drift_detectors, list):
                    for detector in drift_detectors:
                        if detector.get("acronym") == selected_estimator:
                            return {
                                "name": detector.get("name", "Unknown Metric"),
                                "method": detector.get("method", {}),
                                "configuration": detector.get("configuration", {}),
                                "implementation_notes": detector.get("implementation_notes", [])
                            }
            except Exception as e:
                logging.error(f"Error retrieving metric information {selected_estimator}: {e}")
        
        logging.warning(f"Metric not found: {selected_estimator}. Available data: {self.configurations_monitoring}")
        return default_response

