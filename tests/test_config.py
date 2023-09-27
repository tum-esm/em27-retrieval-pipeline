import os
import pytest
import tum_esm_utils
from src import custom_types

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)


@pytest.mark.integration
def test_config() -> None:
    custom_types.Config.load()


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_config_template() -> None:
    config = custom_types.Config.load(
        path=os.path.join(PROJECT_DIR, "config", "config.template.json"),
        check_path_existence=False,
    )
    assert config.proffast is not None
    assert config.profiles is not None
    assert config.export is not None
    assert len(config.export.targets) > 0
