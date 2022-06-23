import os
from tqdm import tqdm
from utils import (
    date_string_is_valid,
    process_queue_additions,
    START_DATE,
    SENSORS,
    PIPELINE_DST,
    OUTPUT_DIR,
)


queue_additions = []
for d in tqdm(range(int(START_DATE), 20300000)):
    if not date_string_is_valid(d):
        continue

    for s in SENSORS:
        try:
            # conditions: ifgs exist, failed output exists
            assert os.path.isdir(f"{PIPELINE_DST}/{s}/ifgs/{d}")
            assert os.path.isdir(f"{PIPELINE_DST}/{s}/{OUTPUT_DIR}/failed/{d}")
            queue_additions.append((s, d))
        except AssertionError:
            pass

process_queue_additions(queue_additions)
