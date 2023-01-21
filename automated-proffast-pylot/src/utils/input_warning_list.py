from datetime import datetime
import json
import os
from src import custom_types

# TODO: statically type this class

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
LIST_PATH = f"{PROJECT_DIR}/logs/input-warnings-to-be-resolved.json"


class InputWarningsList:
    @staticmethod
    def _load() -> dict[str, custom_types.InputWarningsDict]:
        try:
            with open(LIST_PATH, "r") as f:
                current_object = json.load(f)
                custom_types.validate_input_warnings(current_object)
                validated_current_object: dict[
                    str, custom_types.InputWarningsDict
                ] = current_object
                return validated_current_object
        except FileNotFoundError:
            InputWarningsList._dump({})
            return {}

    @staticmethod
    def _dump(new_warnings_list: dict[str, custom_types.InputWarningsDict]) -> None:
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
        if f"{sensor}/{date}" in warnings_list:
            del warnings_list[f"{sensor}/{date}"]
            InputWarningsList._dump(warnings_list)
