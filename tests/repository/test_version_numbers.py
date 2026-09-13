import os

import pytest
import tomli
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)


@pytest.mark.order(2)
@pytest.mark.quick
def test_version_numbers() -> None:
    with open(os.path.join(PROJECT_DIR, "pyproject.toml"), "r") as f:
        third_line = f.read().split("\n")[2]
        assert third_line.startswith("version = ")
        full_pyproject_version = third_line.strip('"version = ')
        pyproject_version = ".".join(full_pyproject_version.split(".")[:2])

    with open(os.path.join(PROJECT_DIR, "config", "config.template.toml"), "rb") as f:
        template_config_version = tomli.load(f)["version"]
    assert template_config_version == pyproject_version

    with open(os.path.join(PROJECT_DIR, "packaging", "em27-metadata", "pyproject.toml"), "rb") as f:
        em27_metadata_version = tomli.load(f)["project"]["version"]
    assert em27_metadata_version == full_pyproject_version
