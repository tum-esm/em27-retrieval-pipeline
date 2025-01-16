import os
import pytest
import tum_esm_utils
import src


@pytest.mark.order(2)
@pytest.mark.quick
def test_config_template() -> None:
    config = src.types.Config.load(
        path=tum_esm_utils.files.rel_to_abs_path("../../config/config.template.json"),
        ignore_path_existence=True,
    )
    assert config.retrieval is not None
    assert config.profiles is not None
    assert config.bundles is not None
    assert len(config.bundles) > 0


@pytest.mark.order(2)
@pytest.mark.quick
def test_geoms_metadata_template() -> None:
    src.types.GEOMSMetadata.load(template=True)


@pytest.mark.order(2)
@pytest.mark.quick
def test_calibration_factors_template() -> None:
    calibration_factors_list = src.types.CalibrationFactorsList.load(template=True)
    assert len(calibration_factors_list.root) == 3
    sids = set([cf.sensor_id for cf in calibration_factors_list.root])
    assert len(sids) == 2
