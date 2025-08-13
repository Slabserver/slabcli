import os
import yaml
import logging
from importlib.resources import files

logger = logging.getLogger(__name__)
missing_keys = False

def get_config_path():
    return files("slabcli").joinpath("config.yml")

def load_config():
    config_path = get_config_path()
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
        return config
    
def compute_config_replacements(source_cfg, target_cfg):
    replacements = {}
    missing_keys = False

    def recurse(source, target, path=""):
        nonlocal missing_keys
        # Keys that exist in both
        common_keys = source.keys() & target.keys()
        for key in common_keys:
            source_val = source[key]
            target_val = target[key]
            full_path = f"{path}.{key}" if path else key
            if isinstance(source_val, dict) and isinstance(target_val, dict):
                recurse(source_val, target_val, full_path)
            elif source_val != target_val:
                replacements[source_val] = target_val

        # Log keys missing in source
        missing_in_source = target.keys() - source.keys()
        for key in missing_in_source:
            full_path = f"{path}.{key}" if path else key
            logger.warning(f"Warning: Missing values in source config: {full_path}")
            missing_keys = True
        
        # Log keys missing in target
        missing_in_target = source.keys() - target.keys()
        for key in missing_in_target:
            full_path = f"{path}.{key}" if path else key
            logger.warning(f"Missing in target config: {full_path}")
            missing_keys = True

    recurse(source_cfg, target_cfg)
    return replacements, missing_keys