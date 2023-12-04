from typing import Optional, Generator
import contextlib
import datetime
import os
import filelock
import pydantic
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)


class RetrievalStatus(pydantic.BaseModel):
    container_id: Optional[str] = None
    sensor_id: str
    from_datetime: datetime.datetime
    location_id: str
    ifg_count: Optional[int] = None
    process_start_time: Optional[datetime.datetime] = None
    process_end_time: Optional[datetime.datetime] = None


class RetrievalStatusList(pydantic.RootModel[list[RetrievalStatus]]):
    root: list[RetrievalStatus]

    @staticmethod
    @contextlib.contextmanager
    def with_filelock() -> Generator[None, None, None]:
        try:
            with filelock.FileLock(
                os.path.join(
                    _PROJECT_DIR, "data", "logs", "active-processes.json.lock"
                ),
                timeout=15,
            ):
                yield
        except TimeoutError:
            pass

    @staticmethod
    def load() -> list[RetrievalStatus]:
        with RetrievalStatus.with_filelock():
            try:
                with open("data/logs/active-processes.json", "r") as f:
                    return RetrievalStatus.model_validate_json(f.read()).root
            except pydantic.ValidationError:
                return []

    @staticmethod
    def reset() -> None:
        with RetrievalStatusList.with_filelock():
            with open("data/logs/active-processes.json", "w") as f:
                f.write("[]")

    @staticmethod
    def add_items(items: list[tuple[str, datetime.datetime, str]]) -> None:
        """Add items to the active process list.
        
        Args:
            items: A list of tuples of the form (sensor_id, date, location_id)."""
        with RetrievalStatusList.with_filelock():
            try:
                with open("data/logs/active-processes.json", "r") as f:
                    process_list = RetrievalStatusList.model_validate_json(
                        f.read()
                    )
            except pydantic.ValidationError:
                return
            for sensor_id, from_datetime, location_id in items:
                process_list.root.append(
                    RetrievalStatus(
                        sensor_id=sensor_id,
                        from_datetime=from_datetime,
                        location_id=location_id,
                    )
                )
            with open("data/logs/active-processes.json", "w") as f:
                f.write(process_list.model_dump_json(indent=4))

    @staticmethod
    def update_item(
        sensor_id: str,
        from_datetime: datetime.datetime,
        container_id: Optional[str] = None,
        ifg_count: Optional[int] = None,
        process_start_time: Optional[datetime.datetime] = None,
        process_end_time: Optional[datetime.datetime] = None
    ) -> None:
        try:
            with open("data/logs/active-processes.json", "r") as f:
                process_list = RetrievalStatusList.model_validate_json(f.read())
        except pydantic.ValidationError:
            return
        for p in process_list.root:
            if p.sensor_id == sensor_id and p.from_datetime == from_datetime:
                if container_id is not None:
                    p.container_id = container_id
                if ifg_count is not None:
                    p.ifg_count = ifg_count
                if process_start_time is not None:
                    p.process_start_time = process_start_time
                if process_end_time is not None:
                    p.process_end_time = process_end_time
                break
        with open("data/logs/active-processes.json", "w") as f:
            f.write(process_list.model_dump_json(indent=4))
