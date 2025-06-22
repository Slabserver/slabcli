import os
import yaml
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("config.yml")

def load_config():
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)
        # print(config["replacements"])  # This should work if config is a dict
        return config
    
def compute_config_replacements(source_cfg, target_cfg):
    replacements = {}
    for key in source_cfg.keys() & target_cfg.keys():
        source_val = source_cfg[key]
        target_val = target_cfg[key]
        if target_val != source_val:
            replacements[target_val] = source_val
    return replacements
