import logging
from Dashboard.config import BASE_URL_API
from Dashboard.utils.utils_apiclient import ApiClient

logger = logging.getLogger(__name__)


class ModelInformation:

    def __init__(self, project_id: str):
        self.api_client = ApiClient(BASE_URL_API)
        self.project_id = project_id

    
    # =====================================================
    # INTERNAL
    # =====================================================
    def _get_all_configurations(self):
        try:
            return self.api_client.get(
                f"{self.project_id}/models_full/"
            )
        except Exception as e:
            logger.error(f"Error fetching full models: {e}")
            return []
    
    # =====================================================
    # GET CONFIGURATIONS
    # =====================================================

    def get_configuration_by_model_id(self, model_id: str):
        try:
            return self.api_client.get(
                f"{self.project_id}/metadata/{model_id}"
            )
        except Exception as e:
            logger.error(f"Error getting config by id: {e}")
            return None

    def get_configuration_by_model_name(self, model_name: str):
        configs = self._get_all_configurations()

        for config in configs:
            if config.get("ml_model_configuration", {}).get("model_identification", {}).get("ID") == model_name:
                return config

        return None

    # =====================================================
    # DROPDOWN OPTIONS
    # =====================================================
    def get_model_name_options(self):
        configs = self._get_all_configurations()

        unique_models = {}

        for cfg in configs:
            ml_config = cfg.get("ml_model_configuration", {})
            desc = ml_config.get("model_description", {})
            ident = ml_config.get("model_identification", {})

            name = desc.get("model_name")
            model_id = ident.get("ID")  # ⚠️ En tu JSON es "ID", no "model_ID"

            if name and model_id:
                unique_models[model_id] = name

        return [
            {"label": name, "value": model_id}
            for model_id, name in sorted(unique_models.items(), key=lambda x: x[1])
        ]

    def get_model_id_options(self):
        configs = self._get_all_configurations()

        options = []

        for config in configs:
            model_id = config.get("ml_model_configuration", {}).get("model_identification", {}).get("ID")
            model_name = config.get("ml_model_configuration", {}).get("model_description", {}).get("model_name")

            if model_id and model_name:
                options.append({
                    "label": model_name,
                    "value": model_id
                })

        return options

    def get_languages_for_model(self, model_name: str):
        configs = self._get_all_configurations()
        languages = set()

        for config in configs:
            desc = config.get("ml_model_configuration", {}).get("model_description", {})
            if desc.get("model_name") == model_name:
                language = desc.get("language", {}).get("name")
                if language:
                    languages.add(language)

        return sorted(languages)

    # =====================================================
    # INPUTS
    # =====================================================

    def load_inputs_from_configuration(self, model_name: str):
        config = self.get_configuration_by_model_name(model_name) or {}

        features = config.get("ml_model_configuration", {}).get("inputs", {}).get("features", [])

        return [
            {"label": f["name"], "value": f["name"]}
            for f in features
            if "name" in f
        ]

    def get_unique_types_models(self, model_name: str):
        
        config = self.get_configuration_by_model_name(model_name)
        
        if not config:
            return []

        return self.get_feature_categories(config)

    def get_feature_categories(self, config: dict):
        
        categories = {
            feature.get("type")
            for feature in config.get("ml_model_configuration", {}).get("inputs", {}).get("features", [])
            if feature.get("type")
        }

        return list(categories)

    def get_names_by_category(self, category: list, model_name: str):
        config = self.get_configuration_by_model_name(model_name)

        if not config:
            return []

        return [
            {"label": feature["name"], "value": feature["name"]}
            for feature in config.get("ml_model_configuration", {}).get("inputs", {}).get("features", [])
            if feature.get("type") in category
        ]

    # =====================================================
    # PROJECT
    # =====================================================

    def project_details(self):
        try:
            return self.api_client.get(f"{self.project_id}/project_info/")
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return None


# =====================================================
# GLOBAL FUNCTION (STATELESS)
# =====================================================

def list_projects():
    try:
        api_client = ApiClient(BASE_URL_API)
        response = api_client.get("list_projects/")
        return [
            {"name": project["name"], "id": project["project_ID"]}
            for project in response
        ]
    except Exception as e:
        logger.error(f"Error getting project names: {e}")
        return []