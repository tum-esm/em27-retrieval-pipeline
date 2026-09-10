import os
import shutil
import tempfile

import pytest
import tum_esm_utils
import src


_OLD_TEMPLATES_DIR = tum_esm_utils.files.rel_to_abs_path("../../config/old_templates")


def _copy_old_templates(tmp_dir: str, filenames: list[str]) -> None:
    for filename in filenames:
        shutil.copy(os.path.join(_OLD_TEMPLATES_DIR, filename), os.path.join(tmp_dir, filename))


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
def test_automatic_config_conversion() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        _copy_old_templates(
            tmp_dir,
            ["config.json", "locations.json", "sensors.json", "campaigns.json", "events.json"],
        )

        src.types.Config.load(
            path=os.path.join(tmp_dir, "config.json"), ignore_path_existence=True
        )

        converted_config = src.types.Config.model_validate(
            tum_esm_utils.files.load_toml_file(os.path.join(tmp_dir, "config.toml")),
            context={"ignore-path-existence": True},
        )
        expected_config = src.types.Config.model_validate(
            tum_esm_utils.files.load_toml_file(
                os.path.join(_OLD_TEMPLATES_DIR, "config.automatically_converted.toml")
            ),
            context={"ignore-path-existence": True},
        )
        assert converted_config == expected_config


@pytest.mark.order(2)
@pytest.mark.quick
def test_em27_metadata_template() -> None:
    src.em27_metadata.load_from_local_files(
        config_directory=tum_esm_utils.files.rel_to_abs_path("../../config"), template=True
    )


# TODO: test whether loading the old em27 metadata works


@pytest.mark.order(2)
@pytest.mark.quick
def test_geoms_metadata_template() -> None:
    src.types.GEOMSMetadata.load(template=True)


@pytest.mark.order(2)
@pytest.mark.quick
def test_automatic_geoms_metadata_conversion(monkeypatch: pytest.MonkeyPatch) -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        _copy_old_templates(tmp_dir, ["geoms_metadata.json", "calibration_factors.json"])
        monkeypatch.setenv("ERP_CONFIG_DIR", tmp_dir)

        src.types.GEOMSMetadata.load()

        converted_metadata = tum_esm_utils.files.load_toml_file(
            os.path.join(tmp_dir, "geoms_metadata.toml")
        )
        expected_metadata = tum_esm_utils.files.load_toml_file(
            os.path.join(_OLD_TEMPLATES_DIR, "geoms_metadata.automatically_converted.toml")
        )
        assert converted_metadata == expected_metadata
