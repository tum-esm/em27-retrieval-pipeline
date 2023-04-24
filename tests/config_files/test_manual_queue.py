import json
import os
import pytest
import tum_esm_em27_metadata
import tum_esm_utils
from src import custom_types


PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
MANUAL_QUEUE_FILE = os.path.join(PROJECT_DIR, "config", "manual-queue.json")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "config.json")


@pytest.mark.integration
def test_manual_queue() -> None:
    if not os.path.isfile(MANUAL_QUEUE_FILE):
        return

    with open(MANUAL_QUEUE_FILE, "r") as f:
        manual_queue = custom_types.ManualQueue(items=json.load(f))

    with open(CONFIG_PATH, "r") as f:
        config = custom_types.Config(**json.load(f))

    # test whether metadata can be loaded
    em27_metadata = tum_esm_em27_metadata.load_from_github(
        **config.general.location_data.dict()
    )

    for item in manual_queue.items:
        assert (
            item.sensor_id in em27_metadata.sensor_ids
        ), f'Sensor ID "{item.sensor_id}" not found in metadata'
