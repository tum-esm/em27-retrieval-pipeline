import os
import sys
import json
from datetime import datetime


dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
MANUAL_QUEUE_PATH = f"{PROJECT_DIR}/config/manual-queue.json"
sys.path.append(PROJECT_DIR)
from src import utils

CONFIG = utils.load_config(validate=True)
SENSORS = CONFIG["sensors_to_consider"]
START_DATE = CONFIG["start_date"]
PIPELINE_DST = CONFIG["dst"]
OUTPUT_DIR = "proffast-2.2-outputs"
PRIORITY = -5


def _load_queue() -> list:
    with open(MANUAL_QUEUE_PATH, "r") as f:
        return json.load(f)


def _save_queue(queue: list):
    with open(MANUAL_QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=4)


def _add_to_queue(queue, sensor, date):
    queue = list(
        filter(
            lambda x: not ((x["sensor"] == sensor) and (x["date"] == str(date))),
            queue,
        )
    )
    queue.append({"sensor": sensor, "date": str(date), "priority": PRIORITY})
    return queue


def date_string_is_valid(date_string):
    try:
        datetime.strptime(str(date_string), "%Y%m%d")
        return True
    except:
        return False


def process_queue_additions(queue_additions: list):
    queue = _load_queue()
    for s, d in queue_additions:
        queue = _add_to_queue(queue, s, d)
    _save_queue(queue)
    print(
        f"proffast_version = 2.2, start_date = {START_DATE}\n"
        f"Added {len(queue_additions)} timeseries to queue:\n"
        + " ".join([f"{s}/{d}" for s, d in queue_additions])
    )
