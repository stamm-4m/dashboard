from Dashboard.utils.utils_model_information import ModelInformation
from Dashboard.utils.model_config_loader import ModelConfigLoader

config_loader = ModelConfigLoader()
model_selector = config_loader
#model_selector.load_multiple_yaml_files('../ML_Repository')


model_information = ModelInformation()
        