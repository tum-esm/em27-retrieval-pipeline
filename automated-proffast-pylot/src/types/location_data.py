import json
import os
import subprocess
from typing import Any, TypedDict
from .validation_error import ValidationError
from .config import ConfigDict

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


class LocationCoordinatesDict(TypedDict):
    details: str
    lon: float
    lat: float
    alt: int


class _LocationTimeFrame(TypedDict):
    from_date: str
    to_date: str
    location: str


class _UTCOffsetTimeFrame(TypedDict):
    from_date: str
    to_date: str
    utc_offset: float


class SensorLocationDict(TypedDict):
    serial_number: int
    utc_offsets: list[_UTCOffsetTimeFrame]
    locations: list[_LocationTimeFrame]


def validate_location_data(config: ConfigDict) -> None:
    """
    Check, whether a given list is a correct list of ManualQueueItemDicts
    Raises a pydantic.ValidationError if the object is invalid.

    This should always be used when loading the object from a
    JSON file!
    """

    try:
        location_repo_pytest = subprocess.run(
            ["python", "-m", "pytest", "tests"],
            cwd=os.path.join(PROJECT_DIR, "location-data"),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        assert location_repo_pytest.returncode == 0, (
            f"pytests on location repo failed: "
            + f"stdout={location_repo_pytest.stdout.decode()}, "
            + f"stderr={location_repo_pytest.stderr.decode()}"
        )

        with open(f"{PROJECT_DIR}/location-data/data/sensors.json") as f:
            sensors = json.load(f)

        for sensor in config["sensors_to_consider"]:
            assert sensor in sensors.keys(), f'no location data for sensor "{sensor}"'

    except AssertionError as e:
        raise ValidationError(f"location repo is invalid: {e}")
