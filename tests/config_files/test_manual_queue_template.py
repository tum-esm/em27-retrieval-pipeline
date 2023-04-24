import json
import os
import pytest
import tum_esm_utils
from src import custom_types

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
MANUAL_QUEUE_TEMPLATE_FILE = os.path.join(
    PROJECT_DIR, "config", "manual-queue.template.json"
)


@pytest.mark.ci
def test_manual_queue_template() -> None:
    with open(MANUAL_QUEUE_TEMPLATE_FILE, "r") as f:
        custom_types.ManualQueue(items=json.load(f))
