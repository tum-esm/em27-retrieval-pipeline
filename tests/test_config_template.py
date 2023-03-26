import json
import os
import pytest
import tum_esm_utils
from src import custom_types

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)


@pytest.mark.ci
def test_default_config() -> None:
    with open(os.path.join(PROJECT_DIR, "config", "config.template.json"), "r") as f:
        config_file_content = json.load(f)
    config_file_content["general"]["data_src_dirs"]["datalogger"] = PROJECT_DIR
    config_file_content["general"]["data_src_dirs"]["vertical_profiles"] = PROJECT_DIR
    config_file_content["general"]["data_src_dirs"]["interferograms"] = PROJECT_DIR
    config_file_content["general"]["data_dst_dirs"]["results"] = PROJECT_DIR

    assert len(config_file_content["output_merging_targets"]) == 1
    config_file_content["output_merging_targets"][0]["dst_dir"] = PROJECT_DIR

    custom_types.Config(**config_file_content)
