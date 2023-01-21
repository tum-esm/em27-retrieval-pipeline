import json
import os
import pytest
from src import custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


@pytest.mark.integration
def test_default_config() -> None:
    with open(os.path.join(PROJECT_DIR, "config", "config.json"), "r") as f:
        config = json.load(f)
    custom_types.validate_config_dict(config)
