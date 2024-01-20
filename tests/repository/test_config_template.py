import pytest
import tum_esm_utils
import src


@pytest.mark.order(2)
@pytest.mark.quick
def test_config_template() -> None:
    config = src.types.Config.load(
        path=tum_esm_utils.files.
        rel_to_abs_path("../../config/config.template.json"),
        ignore_path_existence=True,
    )
    assert config.retrieval is not None
    assert config.profiles is not None
    assert config.export_targets is not None
    assert len(config.export_targets) > 0
