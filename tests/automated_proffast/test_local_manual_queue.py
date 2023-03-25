import json
import os
import pytest
from src import custom_types

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(os.path.abspath(__file__)))
MANUAL_QUEUE_FILE = os.path.join(PROJECT_DIR, "config", "manual-queue.json")


@pytest.mark.integration
def test_local_config() -> None:
    if os.path.isfile(MANUAL_QUEUE_FILE):
        with open(MANUAL_QUEUE_FILE, "r") as f:
            custom_types.ManualQueue(items=json.load(f))
