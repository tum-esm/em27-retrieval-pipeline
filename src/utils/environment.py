import os

import tum_esm_utils


CONFIG_DIR_KEY = "ERP_CONFIG_DIR"
DEFAULT_CONFIG_DIR = tum_esm_utils.files.rel_to_abs_path("../../config")


def get_config_dir() -> str:
    return os.getenv(CONFIG_DIR_KEY, DEFAULT_CONFIG_DIR)


def get_config_path() -> str:
    return os.path.join(
        os.getenv(CONFIG_DIR_KEY, DEFAULT_CONFIG_DIR),
        "config.json"
    )
