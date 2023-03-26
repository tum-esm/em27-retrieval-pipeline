import json
import os
import tum_esm_utils
from typing import Optional
from src import custom_types, utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
MANUAL_QUEUE_FILE = os.path.join(PROJECT_DIR, "config", "manual-queue.json")


class ManualQueueInterface:
    """Interface for the manual queue file.

    An example of the manual queue (`config/manual-queue.json`) content:

    ```json
    [
        {
            "sensor_id": "some_sensor_id",
            "date": "20210101",
            "priority": 1
        },
        {
            "sensor_id": "some_sensor_id",
            "date": "20210101",
            "priority": -2
        }
    ]
    """

    @staticmethod
    def _load(
        logger: utils.automated_proffast.Logger,
    ) -> Optional[custom_types.ManualQueue]:
        if not os.path.isfile(MANUAL_QUEUE_FILE):
            return None

        try:
            with open(MANUAL_QUEUE_FILE, "r") as f:
                return custom_types.ManualQueue(items=json.load(f))
        except Exception:
            logger.error("manual queue is no readable")
            logger.exception()
            return None

    @staticmethod
    def _dump(items: list[custom_types.ManualQueueItem]) -> None:
        with open(MANUAL_QUEUE_FILE, "w") as f:
            json.dump([i.dict() for i in items], f, indent=4)

    @staticmethod
    def get_items(
        logger: utils.automated_proffast.Logger,
    ) -> list[custom_types.ManualQueueItem]:
        """Return the items in the manual queue.

        The items are sorted by priority (highest first) and then by date
        (newest first)."""

        manual_queue = ManualQueueInterface._load(logger)
        if manual_queue is None or len(manual_queue.items) == 0:
            return []

        return list(
            sorted(
                manual_queue.items, key=lambda x: f"{x.priority}{x.date}", reverse=True
            )
        )

    @staticmethod
    def remove_item(
        sensor_id: str, date: str, logger: utils.automated_proffast.Logger
    ) -> None:
        """Remove an item from the manual queue."""

        manual_queue = ManualQueueInterface._load(logger)
        if manual_queue is None:
            return None

        new_manual_queue_items = list(
            filter(
                lambda i: not ((i.sensor_id == sensor_id) and (i.date == date)),
                manual_queue.items,
            )
        )

        ManualQueueInterface._dump(new_manual_queue_items)
