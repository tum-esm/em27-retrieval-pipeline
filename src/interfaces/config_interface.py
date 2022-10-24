import os
import json
from pathlib import Path

from src import types, utils

PROJECT_DIR = Path(os.path.abspath(__file__)).parents[2]
CONFIG_FILE_PATH = os.path.join(PROJECT_DIR, "config", "config.json")
CONFIG_LOCK_PATH = os.path.join(PROJECT_DIR, "config", ".config.lock")

class ConfigInterface:
    @staticmethod
    @utils.with_filelock(CONFIG_LOCK_PATH, timeout=10)
    def read() -> types.ConfigDict:
        """
        Read the contents of the current config.json file.
        The function will validate its integrity and raises
        an Exception if the file is not valid.
        """
        with open(CONFIG_FILE_PATH, "r") as f:
            o = json.load(f)
            types.validate_config_dict(o)
            config: types.ConfigDict = o
            
        return config #NOTE - Shallow copy?
