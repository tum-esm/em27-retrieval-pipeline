import pytest
import tum_esm_utils
import src


@pytest.mark.order(2)
@pytest.mark.quick
def test_config_template() -> None:
    config = src.types.Config.load(
        path=tum_esm_utils.files.rel_to_abs_path("../../config/config.template.toml"),
        ignore_path_existence=True,
    )
    assert config.retrieval is not None
    assert config.ggg_profiles_downloader is not None
    assert len(config.bundle_exports) > 0


@pytest.mark.order(2)
@pytest.mark.quick
def test_geoms_metadata_template() -> None:
    src.types.GEOMSMetadata.load(template=True)
