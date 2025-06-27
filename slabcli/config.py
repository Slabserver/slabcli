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
    for key in source_cfg.keys() & target_cfg.keys():
        source_val = source_cfg[key]
        target_val = target_cfg[key]
        if target_val != source_val:
            replacements[target_val] = source_val
    return replacements
