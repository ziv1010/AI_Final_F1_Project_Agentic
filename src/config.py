import yaml
import os
from pathlib import Path

def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

CONFIG = load_config()

def get_raw_data_path():
    return Path(os.getcwd()) / CONFIG["data"]["raw_path"]

def get_cache_path():
    return Path(os.getcwd()) / CONFIG["data"]["cache_path"]

def get_outputs_path():
    return Path(os.getcwd()) / CONFIG["data"]["outputs_path"]
