import json
import os
import pytest
import tum_esm_utils
import tum_esm_em27_metadata
from src import custom_types

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")


@pytest.mark.integration
def test_config():
    with open(CONFIG_PATH, "r") as f:
        config = custom_types.Config(**json.load(f))

    # test whether metadata can be loaded
    em27_metadata = tum_esm_em27_metadata.load_from_github(
        **config.general.location_data.dict()
    )

    # test whether from_dates are before to_dates
    assert (
        config.vertical_profiles.request_scope.from_date
        <= config.vertical_profiles.request_scope.to_date
    )
    assert (
        config.automated_proffast.data_filter.from_date
        <= config.automated_proffast.data_filter.to_date
    )

    # test whether sensor_ids and campaign_ids are in metadata
    for sensor_id in config.automated_proffast.data_filter.sensor_ids_to_consider:
        assert (
            sensor_id in em27_metadata.sensor_ids
        ), f"sensor_id not in metadata: {sensor_id}"

    for t in config.output_merging_targets:
        assert (
            t.campaign_id in em27_metadata.campaign_ids
        ), f"campaign_id not in metadata: {t.campaign_id}"
