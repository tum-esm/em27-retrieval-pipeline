import pytest
import tum_esm_utils
from src import types


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_config_template() -> None:
    config = types.Config.load(
        path=tum_esm_utils.files.
        rel_to_abs_path("../../config/config.template.json"),
        ignore_path_existence=True,
    )
    assert config.retrieval is not None
    assert config.profiles is not None
    assert config.export_targets is not None
    assert len(config.export_targets) > 0
