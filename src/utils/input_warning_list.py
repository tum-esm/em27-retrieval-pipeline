from datetime import datetime
import json
import os
from typing import Any

# TODO: statically type this class

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
LIST_PATH = f"{PROJECT_DIR}/logs/input-warnings-to-be-resolved.json"


class InputWarningsList:
    @staticmethod
    def _load() -> dict[str, Any]:
        try:
            with open(LIST_PATH, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            InputWarningsList._dump({})
            return {}

    @staticmethod
    def _dump(new_warnings_list: dict[str, Any]) -> None:
        with open(LIST_PATH, "w") as f:
            json.dump(new_warnings_list, f, indent=4)

    @staticmethod
    def add(sensor: str, date: str, message: str) -> None:
        warnings_list = InputWarningsList._load()
        t = datetime.utcnow().strftime("%Y%m%d %H:%M:%S UTC")
        warnings_list[f"{sensor}/{date}"] = {"message": message, "last_checked": t}
        InputWarningsList._dump(warnings_list)

    @staticmethod
    def remove(sensor: str, date: str) -> None:
        warnings_list = InputWarningsList._load()
        del warnings_list[f"{sensor}/{date}"]
        InputWarningsList._dump(warnings_list)
