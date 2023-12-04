import os
import datetime
import tum_esm_utils
from src import types

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)
_LIST_PATH = os.path.join(
    _PROJECT_DIR, "logs", "retrieval", "input-warnings-to-be-resolved.json"
)


class InputWarningsInterface:
    @staticmethod
    def _load() -> types.InputWarningsList:
        try:
            with open(_LIST_PATH, "r") as f:
                return types.InputWarningsList.model_validate_json(f.read())
        except FileNotFoundError:
            return types.InputWarningsList(root=[])
        except Exception as e:
            raise ValueError(
                f"inputs warnings list not in the right format: {e}"
            )

    @staticmethod
    def _dump(new_object: types.InputWarningsList) -> None:
        tum_esm_utils.files.dump_json_file(
            _LIST_PATH,
            new_object.model_dump()["items"]
        )

    @staticmethod
    def add(
        sensor_id: str, from_datetime: datetime.datetime, message: str
    ) -> None:
        warnings_list = InputWarningsInterface._load()
        warnings_list.items = list(
            filter(
                lambda w: not ((w.sensor_id == sensor_id) and
                               (w.from_datetime == from_datetime)),
                warnings_list.items,
            )
        )
        warnings_list.items.append(
            types.InputWarning(
                sensor_id=sensor_id,
                from_datetime=from_datetime,
                message=message,
                last_checked=datetime.datetime.utcnow(),
            )
        )
        InputWarningsInterface._dump(warnings_list)

    @staticmethod
    def remove(sensor_id: str, from_datetime: datetime.datetime) -> None:
        warnings_list = InputWarningsInterface._load()
        warnings_list.items = list(
            filter(
                lambda w: not ((w.sensor_id == sensor_id) and
                               (w.from_datetime == from_datetime)),
                warnings_list.items,
            )
        )
        InputWarningsInterface._dump(warnings_list)
