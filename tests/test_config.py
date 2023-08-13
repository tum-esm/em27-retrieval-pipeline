import os
import pytest
import tum_esm_utils
from src import custom_types

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)


@pytest.mark.integration
def test_config() -> None:
    custom_types.Config.load()


@pytest.mark.ci
def test_config_template() -> None:
    config = custom_types.Config.load(
        path=os.path.join(PROJECT_DIR, "config", "config.template.json"),
        check_path_existence=False,
    )
    assert config.automated_proffast is not None
    assert config.vertical_profiles is not None
    assert len(config.output_merging_targets) > 0
