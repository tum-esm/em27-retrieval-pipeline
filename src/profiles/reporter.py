from __future__ import annotations
from typing import Any, Literal, Optional
import os
import copy
import json
import datetime
import tum_esm_utils
import src

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)
_REPORT_PATH = os.path.join(_PROJECT_DIR, "logs", "profiles")


class Reporter:
    """Generates reports."""
    def __init__(
        self,
        query_list: list[src.utils.types.DownloadQuery],
        version: Literal["GGG2014", "GGG2020"],
    ) -> None:
        self._version = version
        self._query_list = copy.deepcopy(query_list)
        self._successful_queries: list[dict[str, Any]] = []
        self._exec_start = datetime.datetime.utcnow()

    def __enter__(self) -> Reporter:
        return self

    def report_query(
        self,
        query: src.utils.types.DownloadQuery,
        up_status: bool,
        up_time: float,
        down_status: bool,
        down_time: float,
        to_date: Optional[datetime.date],
    ) -> None:
        """Appends query statistics to the report."""
        truncated: Optional[datetime.date] = None
        if (to_date is not None) and (query.to_date != to_date):
            truncated = to_date

        self._successful_queries.append(
            query.model_dump() | {
                "up_status": up_status,
                "up_time": str(datetime.timedelta(seconds=up_time)),
                "down_status": down_status,
                "down_time": str(datetime.timedelta(seconds=down_time)),
                "truncated": truncated,
            }
        )
        self._query_list.remove(query)

    def __exit__(self, exc_type: Any, *_: Any) -> None:
        success = False if exc_type or self._query_list else True
        exec_start_str = self._exec_start.strftime("%Y%m%d%H%M")
        execution_time = str(datetime.datetime.utcnow() - self._exec_start)

        with open(
            f"{_REPORT_PATH}/{self._version}/{exec_start_str}.json", "w"
        ) as report:
            json.dump(
                {
                    "success":
                        success,
                    "execution_start":
                        exec_start_str,
                    "execution_time":
                        execution_time,
                    "successful_queries":
                        self._successful_queries,
                    "failed_queries":
                        [query.model_dump_json() for query in self._query_list],
                },
                report,
                indent=4,
            )
