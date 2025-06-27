import os
import yaml
from importlib.resources import files

config_path = files("slabcli").joinpath("config.yml")

def load_config():
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
        return config
    
def compute_config_replacements(source_cfg, target_cfg):
    replacements = {}

    def recurse(source, target):
        for key in source.keys() & target.keys():
            source_val = source[key]
            target_val = target[key]
            if isinstance(source_val, dict) and isinstance(target_val, dict):
                recurse(source_val, target_val)
            elif source_val != target_val:
                replacements[target_val] = source_val

    recurse(source_cfg, target_cfg)
    return replacements