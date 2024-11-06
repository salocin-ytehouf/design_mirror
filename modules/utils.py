# modules/utils.py

import yaml
import logging

def load_config_file(config_path='config.yaml'):
    """Load configuration from a YAML file."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        logging.info(f"Configuration loaded from {config_path}")
        return config
    except Exception as e:
        logging.error(f"Failed to load configuration file {config_path}: {e}")
        raise
