import json
import os
from typing import Optional
from src import custom_types, utils
import filelock

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
MANUAL_QUEUE_FILE = os.path.join(PROJECT_DIR, "config", "manual-queue.json")

lock = filelock.FileLock(os.path.join(PROJECT_DIR, "config", "manual-queue.json"))


class ManualQueueInterface:
    @staticmethod
    def load(logger: utils.Logger) -> Optional[custom_types.ManualQueue]:
        if not os.path.isfile(MANUAL_QUEUE_FILE):
            logger.debug(f"No manual queue file")
            return None

        try:
            with open(MANUAL_QUEUE_FILE, "r") as f:
                return custom_types.ManualQueue(items=json.load(f))
        except Exception as e:
            logger.warning(f"Manual queue in an invalid format: {e}")
            return None

    @staticmethod
    def dump(items: list[custom_types.ManualQueueItem]) -> None:
        with open(MANUAL_QUEUE_FILE, "w") as f:
            json.dump(items, f, indent=4)

    @staticmethod
    def get_next_item(logger: utils.Logger) -> Optional[custom_types.ManualQueueItem]:
        manual_queue = ManualQueueInterface.load(logger)
        if manual_queue is None or len(manual_queue.items) == 0:
            return None

        # highest priority first, then newest date first
        return list(
            sorted(
                manual_queue.items, key=lambda x: f"{x.priority}{x.date}", reverse=True
            )
        )[0]

    @staticmethod
    def remove_item(sensor_id: str, date: str, logger: utils.Logger) -> None:
        manual_queue = ManualQueueInterface.load(logger)

        new_manual_queue_items = list(
            filter(
                lambda i: not ((i.sensor_id == sensor_id) and (i.date == date)),
                manual_queue.items,
            )
        )

        ManualQueueInterface.dump(new_manual_queue_items)
