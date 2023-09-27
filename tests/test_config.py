import os
import pytest
import tum_esm_utils
from src import utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)


@pytest.mark.integration
def test_config() -> None:
    utils.config.Config.load()


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_config_template() -> None:
    config = utils.config.Config.load(
        path=os.path.join(PROJECT_DIR, "config", "config.template.json"),
        check_path_existence=False,
    )
    assert config.retrieval is not None
    assert config.profiles is not None
    assert config.export is not None
    assert len(config.export.targets) > 0
