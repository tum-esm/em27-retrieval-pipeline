import json
import os
import tum_esm_utils
import tum_esm_em27_metadata
from src import custom_types

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")


def test_config():
    with open(CONFIG_PATH, "r") as f:
        config = custom_types.Config(**json.load(f))

    tum_esm_em27_metadata.load_from_github(**config.location_data.dict())
