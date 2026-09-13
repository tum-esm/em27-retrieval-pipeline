import datetime
from typing import Literal


DATE_STRING_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
UTC_DATETIME_STRING_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+0000)$"


def parse_date_string(value: str) -> datetime.date:
    return datetime.datetime.strptime(value, "%Y-%m-%d").date()


def parse_datetime_string(value: str) -> datetime.datetime:
    return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")


RetrievalAlgorithm = Literal[
    "proffast-1.0",
    "proffast-2.2",
    "proffast-2.3",
    "proffast-2.4",
    "proffast-2.4.1",
]
AtmosphericProfileModel = Literal[
    "GGG2014",
    "GGG2020",
]
