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


# TODO: test whether loading the old config works


@pytest.mark.order(2)
@pytest.mark.quick
def test_em27_metadata_template() -> None:
    src.em27_metadata.load_from_local_files(
        config_directory=tum_esm_utils.files.rel_to_abs_path("../../config")
    )


# TODO: test whether loading the old em27 metadata works


@pytest.mark.order(2)
@pytest.mark.quick
def test_geoms_metadata_template() -> None:
    src.types.GEOMSMetadata.load(template=True)


# TODO: test whether loading the old geoms metadata works
