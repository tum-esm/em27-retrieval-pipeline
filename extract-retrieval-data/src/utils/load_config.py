import json
import os
from src import custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")


def load_config() -> custom_types.Config:
    assert os.path.isfile(CONFIG_PATH), "config.json file does not exist"
    try:
        with open(CONFIG_PATH, "r") as f:
            content_in_config_file = json.load(f)
    except:
        raise Exception("config.json is not in a valid JSON format")

    return custom_types.Config(**content_in_config_file)
