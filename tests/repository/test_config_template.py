import pytest
import tum_esm_utils
import src


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_config_template() -> None:
    config = src.utils.config.Config.load(
        path=tum_esm_utils.files.
        rel_to_abs_path("../../config/config.template.json"),
        check_path_existence=False,
    )
    assert config.retrieval is not None
    assert config.profiles is not None
    assert config.export is not None
    assert len(config.export.targets) > 0
