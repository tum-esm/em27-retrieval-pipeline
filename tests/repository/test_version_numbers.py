import json
import os
import pytest
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)


@pytest.mark.order(2)
@pytest.mark.quick
def test_version_numbers() -> None:
    with open(os.path.join(PROJECT_DIR, "pyproject.toml"), "r") as f:
        third_line = f.read().split("\n")[2]
        assert third_line.startswith("version = ")
        pyproject_version = ".".join(third_line.strip('"version = ').split(".")[:2])

    with open(os.path.join(PROJECT_DIR, "config", "config.template.json"), "r") as f:
        template_config_version = json.load(f)["version"]
    assert template_config_version == pyproject_version
