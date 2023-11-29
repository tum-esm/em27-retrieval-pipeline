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


class ProcessStatus(pydantic.BaseModel):
    container_id: str
    sensor_id: str
    date: datetime.date
    location_id: str
    ifg_count: Optional[int] = None
    process_start_time: Optional[datetime.datetime] = None
    process_end_time: Optional[datetime.datetime] = None


class ProcessStatusList(pydantic.RootModel[list[ProcessStatus]]):
    root: list[ProcessStatus]

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
    def load() -> list[ProcessStatus]:
        with ProcessStatusList.with_filelock():
            try:
                with open("data/logs/active-processes.json", "r") as f:
                    return ProcessStatusList.model_validate_json(f.read()).root
            except pydantic.ValidationError:
                return []

    @staticmethod
    def reset() -> None:
        with ProcessStatusList.with_filelock():
            with open("data/logs/active-processes.json", "w") as f:
                f.write("[]")

    @staticmethod
    def add_item(
        container_id: str,
        sensor_id: str,
        date: datetime.date,
        location_id: str,
    ) -> None:
        with ProcessStatusList.with_filelock():
            try:
                with open("data/logs/active-processes.json", "r") as f:
                    process_list = ProcessStatusList.model_validate_json(
                        f.read()
                    )
            except pydantic.ValidationError:
                return
            process_list.root.append(
                ProcessStatus(
                    container_id=container_id,
                    sensor_id=sensor_id,
                    date=date,
                    location_id=location_id,
                )
            )
            with open("data/logs/active-processes.json", "w") as f:
                f.write(process_list.model_dump_json(indent=4))

    @staticmethod
    def update_item(
        container_id: str,
        ifg_count: Optional[int] = None,
        process_start_time: Optional[datetime.datetime] = None,
        process_end_time: Optional[datetime.datetime] = None
    ) -> None:
        try:
            with open("data/logs/active-processes.json", "r") as f:
                process_list = ProcessStatusList.model_validate_json(f.read())
        except pydantic.ValidationError:
            return
        for p in process_list.root:
            if p.container_id == container_id:
                p.ifg_count = ifg_count
                p.process_start_time = process_start_time
                p.process_end_time = process_end_time
                break
        with open("data/logs/active-processes.json", "w") as f:
            f.write(process_list.model_dump_json(indent=4))
