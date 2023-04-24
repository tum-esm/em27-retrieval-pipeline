import json
import os
import tum_esm_utils
from datetime import datetime
from src import custom_types

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_LIST_PATH = os.path.join(
    _PROJECT_DIR, "logs", "automated_proffast", "input-warnings-to-be-resolved.json"
)


class InputWarningsInterface:
    @staticmethod
    def _load() -> custom_types.InputWarningsList:
        try:
            with open(_LIST_PATH, "r") as f:
                return custom_types.InputWarningsList(items=json.load(f))
        except FileNotFoundError:
            return custom_types.InputWarningsList(items=[])
        except Exception as e:
            raise ValueError(f"inputs warnings list not in the right format: {e}")

    @staticmethod
    def _dump(new_object: custom_types.InputWarningsList) -> None:
        with open(_LIST_PATH, "w") as f:
            json.dump([w.dict() for w in new_object.items], f, indent=4)

    @staticmethod
    def add(sensor_id: str, date: str, message: str) -> None:
        warnings_list = InputWarningsInterface._load()
        warnings_list.items = [
            w
            for w in warnings_list.items
            if not ((w.sensor_id == sensor_id) and (w.date == date))
        ]
        warnings_list.items.append(
            custom_types.InputWarning(
                sensor_id=sensor_id,
                date=date,
                message=message,
                last_checked=datetime.utcnow().strftime("%Y%m%d %H:%M:%S UTC"),
            )
        )
        InputWarningsInterface._dump(warnings_list)

    @staticmethod
    def remove(sensor_id: str, date: str) -> None:
        warnings_list = InputWarningsInterface._load()
        warnings_list.items = [
            w
            for w in warnings_list.items
            if not ((w.sensor_id == sensor_id) and (w.date == date))
        ]
        InputWarningsInterface._dump(warnings_list)
