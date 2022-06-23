from datetime import datetime
import json
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
INPUT_WARNINGS_LIST_PATH = f"{PROJECT_DIR}/logs/input-warnings-to-be-resolved.json"

if not os.path.isfile(INPUT_WARNINGS_LIST_PATH):
    with open(INPUT_WARNINGS_LIST_PATH, "w") as f:
        json.dump([], f)


def _load_warnings_list():
    if not os.path.isfile(INPUT_WARNINGS_LIST_PATH):
        with open(INPUT_WARNINGS_LIST_PATH, "w") as f:
            json.dump([], f)

    with open(INPUT_WARNINGS_LIST_PATH, "r") as f:
        return json.load(f)


def _dump_warnings_list(warnings_list):
    if not os.path.isfile(INPUT_WARNINGS_LIST_PATH):
        with open(INPUT_WARNINGS_LIST_PATH, "w") as f:
            json.dump([], f)

    with open(INPUT_WARNINGS_LIST_PATH, "w") as f:
        json.dump(warnings_list, f, indent=4)


def add_to_input_warnings_list(sensor, date, message):
    warnings_list = _load_warnings_list()
    t = datetime.utcnow().strftime("%Y%m%d %H:%M:%S UTC")
    warnings_list = list(filter(lambda x: x["id"] != f"{sensor}/{date}", warnings_list))
    warnings_list.append(
        {"id": f"{sensor}/{date}", "message": message, "last checked": t}
    )
    _dump_warnings_list(warnings_list)


def remove_from_input_warnings_list(sensor, date):
    warnings_list = _load_warnings_list()
    warnings_list = list(filter(lambda x: x["id"] != f"{sensor}/{date}", warnings_list))
    _dump_warnings_list(warnings_list)
