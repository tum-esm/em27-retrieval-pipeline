import os
from tqdm import tqdm
from utils import (
    date_string_is_valid,
    process_queue_additions,
    START_DATE,
    SENSORS,
    PIPELINE_DST,
)


queue_additions = []
for d in tqdm(range(int(START_DATE), 20300000)):
    if not date_string_is_valid(d):
        continue

    for s in SENSORS:
        try:
            # conditions: ifgs exist, no outputs exist
            assert os.path.isdir(f"{PIPELINE_DST}/{s}/ifgs/{d}")
            assert not os.path.isdir(
                f"{PIPELINE_DST}/{s}/proffast-2.2-outputs/successful/{d}"
            )
            assert not os.path.isdir(
                f"{PIPELINE_DST}/{s}/proffast-2.2-outputs/failed/{d}"
            )
            queue_additions.append((s, d))
        except AssertionError:
            pass

process_queue_additions(queue_additions)
