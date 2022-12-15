from __future__ import annotations

from typing import Any
import os
import copy
import json
from pathlib import Path
from datetime import datetime, timedelta

from src.custom_types import Query, Version

REPORT_PATH = os.path.join(Path(os.path.abspath(__file__)).parents[2], "reports")


class Reporter:
    """Generates reports."""

    def __init__(self, query_list: list[Query], version: Version) -> None:
        self._version = version
        self._query_list = copy.deepcopy(query_list)
        self._successful_queries: list[dict[str, Any]] = []
        self._exec_start = datetime.utcnow()

    def __enter__(self) -> Reporter:
        return self

    def report_query(
        self, query: Query, up_status: bool, up_time: float, down_status: bool, down_time: float
    ) -> None:
        """Appends query statistics to the report."""
        self._successful_queries.append(
            query.to_json()
            | {
                "up_status": up_status,
                "up_time": str(timedelta(seconds=up_time)),
                "down_status": down_status,
                "down_time": str(timedelta(seconds=down_time)),
            }
        )
        self._query_list.remove(query)

    def __exit__(self, exc_type: Any, *_: Any) -> None:

        success = False if exc_type or self._query_list else True
        exec_start_str = self._exec_start.strftime("%Y%m%d %H:%M")
        execution_time = str(datetime.utcnow() - self._exec_start)

        with open(f"{REPORT_PATH}/{self._version}/{exec_start_str}.json", "w") as report:
            json.dump(
                {
                    "success": success,
                    "executionStart": exec_start_str,
                    "executionTime": execution_time,
                    "successful_queries": self._successful_queries,
                    "failed_queries": [query.to_json() for query in self._query_list],
                },
                report,
                indent=4,
            )
