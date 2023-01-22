import json
import os
import pytest
from src import custom_types

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))


@pytest.mark.ci
def test_default_config() -> None:
    with open(os.path.join(PROJECT_DIR, "config", "config.template.json"), "r") as f:
        config_file_content = json.load(f)
    config_file_content["data_src_dirs"]["datalogger"] = PROJECT_DIR
    config_file_content["data_src_dirs"]["vertical_profiles"] = PROJECT_DIR
    config_file_content["data_src_dirs"]["interferograms"] = PROJECT_DIR
    config_file_content["data_dst_dirs"]["results"] = PROJECT_DIR
    custom_types.Config(**config_file_content)
