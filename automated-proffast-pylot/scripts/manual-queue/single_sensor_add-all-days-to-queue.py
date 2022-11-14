import os
from tqdm import tqdm
from utils import (
    date_string_is_valid,
    process_queue_additions,
    START_DATE,
    SENSORS,
    PIPELINE_DST,
)

# define sensor, ma, mb, mc, md, me
single_sensor = "ma"
assert (
    single_sensor in SENSORS
), f"config.sensors_to_consider does not include {single_sensor}"

queue_additions = []
dates = [d for d in range(int(START_DATE), 20300000) if date_string_is_valid(d)]

for date in tqdm(dates):
    # conditions: interferograms exist on long-term storage
    if os.path.isdir(f"{PIPELINE_DST}/{single_sensor}/ifgs/{date}"):
        queue_additions.append((single_sensor, date))

process_queue_additions(queue_additions)
