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
PRIORITY = -5


def date_string_is_valid(date_string):
    try:
        datetime.strptime(str(date_string), "%Y%m%d")
        return True
    except:
        return False


with open(MANUAL_QUEUE_PATH, "r") as f:
    queue: list = json.load(f)


queue_additions = []
for date in tqdm(range(int(START_DATE), 20300000)):
    if not date_string_is_valid(date):
        continue

    for sensor in SENSORS:
        try:
            # conditions: ifgs exist, failed output exists
            assert os.path.isdir(f"{DST}/{sensor}/ifgs/{date}")
            assert os.path.isdir(f"{DST}/{sensor}/{OUTPUT_DIR}/failed/{date}")
            queue_additions.append((sensor, date))
        except AssertionError:
            pass

for s, d in queue_additions:
    queue = list(
        filter(
            lambda x: not ((x["sensor"] == s) and (x["date"] == str(d))),
            queue,
        )
    )
    queue.append({"sensor": s, "date": str(d), "priority": PRIORITY})

print(
    f"Added {len(queue_additions)} timeseries to queue:\n"
    + " ".join([f"{s}/{d}" for s, d in queue_additions])
)

with open(MANUAL_QUEUE_PATH, "w") as f:
    json.dump(queue, f, indent=4)
