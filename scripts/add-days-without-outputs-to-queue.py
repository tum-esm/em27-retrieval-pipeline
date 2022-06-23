import os
import sys
import json
from tqdm import tqdm
from datetime import datetime


dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
MANUAL_QUEUE_PATH = f"{PROJECT_DIR}/config/manual-queue.json"
sys.path.append(PROJECT_DIR)
from src import utils

CONFIG = utils.load_config(validate=True)
SENSORS = CONFIG["sensorsToConsider"]
START_DATE = CONFIG["startDate"]
DST = CONFIG["dst"]
OUTPUT_DIR = {
    "2.0.1": "proffast-2.0-outputs",
    "2.1.1": "proffast-2.1-outputs",
}[CONFIG["proffastVersion"]]


def date_string_is_valid(date_string):
    try:
        datetime.strptime(str(date_string), "%Y%m%d")
        return True
    except:
        return False


with open(MANUAL_QUEUE_PATH, "r") as f:
    queue: list = json.load(f)

    for date in tqdm(range(int(START_DATE), 20300000)):
        if not date_string_is_valid(date):
            continue

        for sensor in SENSORS:
            try:
                # conditions: ifgs exist, no outputs exist
                assert os.path.isdir(f"{DST}/{sensor}/ifgs/{date}")
                assert not os.path.isdir(
                    f"{DST}/{sensor}/{OUTPUT_DIR}/successful/{date}"
                )
                assert not os.path.isdir(f"{DST}/{sensor}/{OUTPUT_DIR}/failed/{date}")
                print(f"Adding {sensor}/{date}")
                queue = list(
                    filter(
                        lambda x: not (
                            (x["sensor"] == sensor) and (x["date"] == str(date))
                        ),
                        queue,
                    )
                )
                queue.append({"sensor": sensor, "date": str(date), "priority": 1})
            except AssertionError:
                pass

with open(MANUAL_QUEUE_PATH, "w") as f:
    json.dump(queue, f, indent=4)
