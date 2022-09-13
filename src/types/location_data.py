import json
import os
import subprocess
from typing import Any, TypedDict
from .validation_error import ValidationError


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

class LocationCoordinatesDict:
    details: str
    lon: float
    lat: float
    alt: int


class _TimeFrame(TypedDict):
    "from": int
    to: int
    location: str
    
class SensorLocationDict:
    serialNumber: int
    locations: list[_TimeFrame]


def validate_location_data(config: dict[str, Any]) -> None:
    """
    Check, whether a given list is a correct list of ManualQueueItemDicts
    Raises a pydantic.ValidationError if the object is invalid.

    This should always be used when loading the object from a
    JSON file!
    """

    try:
        location_repo_pytest = subprocess.run(
            ["python -m pytest tests"],
            cwd=os.path.join(PROJECT_DIR, "location-data"),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        
        assert location_repo_pytest.returncode == 0, f"pytests on location repo failed: stdout={location_repo_pytest.stdout}, stderr={location_repo_pytest.stderr}"
        
        with open(f"{PROJECT_DIR}/location-data/data/sensors.json") as f:
            sensors = json.load(f)
            
        for sensor in config["sensors_to_consider"]:
            assert sensor in sensors.keys(), f'no location data for sensor "{sensor}"'

    except AssertionError as e:
        raise ValidationError(f"location repo is invalid: {e}")
