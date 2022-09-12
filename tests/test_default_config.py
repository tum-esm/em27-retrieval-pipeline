import json
import os
import pytest
from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


@pytest.mark.ci
def test_default_config() -> None:
    with open(os.path.join(PROJECT_DIR, "config", "config.default.json"), "r") as f:
        config = json.load(f)
    types.validate_config_dict(config, skip_filepaths=True)
