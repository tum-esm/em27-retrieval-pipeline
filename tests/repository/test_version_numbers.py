import json
import os
import re

import pytest
import tomli
import tum_esm_utils
import yaml

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

    with open(os.path.join(PROJECT_DIR, "example", "config", "config.toml"), "rb") as f:
        example_config_version = tomli.load(f)["version"]
    assert example_config_version == pyproject_version

    with open(os.path.join(PROJECT_DIR, "packaging", "em27-metadata", "pyproject.toml"), "rb") as f:
        em27_metadata_version = tomli.load(f)["project"]["version"]
    assert em27_metadata_version == full_pyproject_version

    with open(os.path.join(PROJECT_DIR, "CITATION.cff"), "r") as f:
        citation_version = yaml.safe_load(f)["version"]
    assert citation_version == full_pyproject_version

    with open(os.path.join(PROJECT_DIR, "docs", "package.json"), "r") as f:
        docs_package_version = json.load(f)["version"]
    assert docs_package_version == full_pyproject_version

    with open(
        os.path.join(PROJECT_DIR, "docs", "src", "content", "docs", "guides", "quick-start.mdx"),
        "r",
    ) as f:
        quick_start = f.read()
    quick_start_versions = set(
        re.findall(r"(?:\bv|em27-retrieval-pipeline-)(\d+\.\d+\.\d+)", quick_start)
    )
    assert quick_start_versions == {full_pyproject_version}

    with open(
        os.path.join(PROJECT_DIR, ".github", "actions", "validate-metadata", "README.md"),
        "r",
    ) as f:
        action_readme = f.read()
    action_versions = set(
        re.findall(
            r"tum-esm/em27-retrieval-pipeline/"
            r"\.github/actions/validate-metadata@v(\d+\.\d+\.\d+)",
            action_readme,
        )
    )
    assert action_versions == {full_pyproject_version}
