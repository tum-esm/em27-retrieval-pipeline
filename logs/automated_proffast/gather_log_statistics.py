import json
import os
import re
import compact_json
from typing import Optional

import tum_esm_utils


BASE = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=1)

container_log_filepattern = re.compile(r"^\d{8}-\d{2}-\d{2}_[a-z]{10}.log$")
data_context_pattern = re.compile(r"Starting session [^/ ]+/\d{8}")
ifg_count_pattern = re.compile(r" \d+ ifg files found in src directory ([^/]+)")

failed: dict[str, tuple[str, int]] = {}
successful: dict[str, tuple[str, int]] = {}
inputs_incomplete: dict[str, tuple[str, str]] = {}

for log_file in list(sorted(os.listdir(f"{BASE}/archive"))):
    if not container_log_filepattern.match(log_file):
        continue

    with open(f"{BASE}/archive/{log_file}") as f:
        file_content = f.read()

    # LOOK FOR "station_id/date" IDENTIFER

    data_context_pattern_match = data_context_pattern.search(file_content)
    assert (
        data_context_pattern_match is not None
    ), f"No data context found in {BASE}/archive/{log_file}"
    data_context = data_context_pattern_match.group(0).split()[-1]

    # CHECK IF INPUT WERE INCOMPLETE

    input_incomplete_message: Optional[tuple[str, str]] = None
    for input_incomplete_type in ["vertical profiles", "datalogger files", "ifg files"]:
        if f"WARNING - Inputs incomplete ({input_incomplete_type})" in file_content:
            input_incomplete_message = f"({input_incomplete_type})"

    if input_incomplete_message is not None:
        inputs_incomplete[data_context] = (log_file, input_incomplete_message)
        continue

    # LOOK FOR IFG COUNT

    ifg_count_match = ifg_count_pattern.search(file_content)
    assert (
        ifg_count_match is not None
    ), f"No ifg count found in {BASE}/archive/{log_file}"
    ifg_count = int(ifg_count_match.group(0).split()[0])

    if "Pylot execution was successful" in file_content:
        successful[data_context] = (log_file, ifg_count)
    else:
        failed[data_context] = (log_file, ifg_count)

successful_ifg_count = sum([v[1] for v in successful.values()])
failed_ifg_count = sum([v[1] for v in failed.values()])
ifg_success_rate = f"{round((successful_ifg_count / (successful_ifg_count + failed_ifg_count)) * 100, 2)} %"
day_success_rate = (
    f"{round((len(successful) / (len(successful) + len(failed))) * 100, 2)} %"
)


print("successful ifg count =", successful_ifg_count)
print("failed ifg count =", failed_ifg_count)
print(f"ifg success rate = {ifg_success_rate}")
print(f"day success rate = {day_success_rate}")

with open(f"{BASE}/log_statistics.json", "w") as f:
    f.write(
        compact_json.Formatter(max_inline_length=70).serialize(
            json.loads(
                json.dumps(
                    {
                        "dayStatistics": {
                            "successfulCount": len(successful),
                            "failedCount": len(failed),
                            "inputsIncompleteCount": len(inputs_incomplete),
                            "daySuccessRate": day_success_rate,
                        },
                        "ifgStatistics": {
                            "successfulCount": successful_ifg_count,
                            "failedCount": failed_ifg_count,
                            "successRate": ifg_success_rate,
                        },
                        "raw": {
                            "successful": successful,
                            "failed": failed,
                            "inputsIncomplete": inputs_incomplete,
                        },
                    },
                    sort_keys=True,
                )
            ),
        )
    )
