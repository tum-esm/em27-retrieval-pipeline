import os
import tum_esm_utils
import datetime
from src import custom_types

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)
_LIST_PATH = os.path.join(
    _PROJECT_DIR, "logs", "proffast", "input-warnings-to-be-resolved.json"
)


class InputWarningsInterface:
    @staticmethod
    def _load() -> custom_types.InputWarningsList:
        try:
            file_content = tum_esm_utils.files.load_json_file(_LIST_PATH)
            assert isinstance(file_content, list)
            return custom_types.InputWarningsList(items=file_content)
        except FileNotFoundError:
            return custom_types.InputWarningsList(items=[])
        except Exception as e:
            raise ValueError(
                f"inputs warnings list not in the right format: {e}"
            )

    @staticmethod
    def _dump(new_object: custom_types.InputWarningsList) -> None:
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
            custom_types.InputWarning(
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
