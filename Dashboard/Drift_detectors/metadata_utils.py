import yaml
from pathlib import Path
import importlib

def load_algorithm_metadata():
    metadata_path = Path(__file__).parent / "algorithm_metadata.yaml"
    with open(metadata_path, "r") as f:
        return yaml.safe_load(f)

def get_algorithm_function(name: str):
    metadata = load_algorithm_metadata()
    algo_info = metadata.get(name.upper())
    if not algo_info:
        raise ValueError(f"Algorithm '{name}' not found in metadata.")
    module = importlib.import_module(algo_info["module"])
    return getattr(module, algo_info["function"])

def get_algorithm_info(name: str):
    metadata = load_algorithm_metadata()
    return metadata.get(name.upper(), {})
