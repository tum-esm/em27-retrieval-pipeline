import os
import shutil
import tempfile

import pytest
import tomli
import tum_esm_utils

import src

_OLD_TEMPLATES_DIR = tum_esm_utils.files.rel_to_abs_path("../../config/old_templates")


def _copy_old_templates(tmp_dir: str, filenames: list[str]) -> None:
    for filename in filenames:
        shutil.copy(os.path.join(_OLD_TEMPLATES_DIR, filename), os.path.join(tmp_dir, filename))


def _load_toml_file(filepath: str) -> dict[str, object]:
    with open(filepath, "rb") as file:
        return tomli.load(file)


def _load_text_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()


def _assert_in_order(text: str, values: list[str]) -> None:
    positions = [text.index(value) for value in values]
    assert positions == sorted(positions)


@pytest.mark.quick
def test_tomli_supports_multiline_inline_tables() -> None:
    assert tomli.loads(
        """custom_ils = {
    ma = {
        channel1_me = 0.9892,
    },
}
"""
    ) == {"custom_ils": {"ma": {"channel1_me": 0.9892}}}


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

        src.types.Config.load(path=os.path.join(tmp_dir, "config.json"), ignore_path_existence=True)

        converted_config = src.types.Config.model_validate(
            _load_toml_file(os.path.join(tmp_dir, "config.toml")),
            context={"ignore-path-existence": True},
        )
        expected_config = src.types.Config.model_validate(
            _load_toml_file(
                os.path.join(_OLD_TEMPLATES_DIR, "config.automatically_converted.toml")
            ),
            context={"ignore-path-existence": True},
        )
        assert converted_config == expected_config
        converted_text = _load_text_file(os.path.join(tmp_dir, "config.toml"))
        _assert_in_order(
            converted_text,
            [
                "# METADATA",
                "# DATA",
                "# GGG PROFILES DOWNLOADER",
                "# RETRIEVAL",
                "# BUNDLE GENERATOR",
                "# GEOMS GENERATOR",
            ],
        )
        assert " = [\n" not in converted_text
        assert "[retrieval.jobs.1.custom_ils]" not in converted_text
        assert "[retrieval.jobs.1.pressure_calibration_factors]" not in converted_text
        assert "[retrieval.jobs.1.pressure_calibration_offsets]" not in converted_text


@pytest.mark.order(2)
@pytest.mark.quick
def test_em27_metadata_template() -> None:
    src.em27_metadata.load_from_local_files(
        config_directory=tum_esm_utils.files.rel_to_abs_path("../../config"), template=True
    )


@pytest.mark.order(2)
@pytest.mark.quick
def test_automatic_em27_metadata_conversion() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        _copy_old_templates(
            tmp_dir,
            ["locations.json", "sensors.json", "campaigns.json", "events.json"],
        )

        src.em27_metadata.load_from_local_files(config_directory=tmp_dir)

        converted_metadata = _load_toml_file(os.path.join(tmp_dir, "em27_metadata.toml"))
        expected_metadata = _load_toml_file(
            os.path.join(_OLD_TEMPLATES_DIR, "em27_metadata.automatically_converted.toml")
        )
        assert converted_metadata == expected_metadata
        converted_text = _load_text_file(os.path.join(tmp_dir, "em27_metadata.toml"))
        _assert_in_order(
            converted_text,
            ["# LOCATIONS", "# SENSORS", "# CAMPAIGNS", "# EVENTS"],
        )
        assert "[[sensors.deployments]]" not in converted_text
        assert 'deployments = [\n    { from_datetime = "' in converted_text
        assert 'sensor_ids = [ "so", "mc" ]' in converted_text
        assert 'location_ids = [ "SOD", "ZEN" ]' in converted_text


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

        converted_metadata = _load_toml_file(os.path.join(tmp_dir, "geoms_metadata.toml"))
        expected_metadata = _load_toml_file(
            os.path.join(_OLD_TEMPLATES_DIR, "geoms_metadata.automatically_converted.toml")
        )
        assert converted_metadata == expected_metadata
        _assert_in_order(
            _load_text_file(os.path.join(tmp_dir, "geoms_metadata.toml")),
            ["# METADATA", "# CALIBRATION FACTORS"],
        )
