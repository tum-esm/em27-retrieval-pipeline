import pytest
from tests.fixtures import wrap_test_with_mainlock, PROJECT_DIR
from src import custom_types, utils

SENSOR_DATA_CONTEXT = custom_types.SensorDataContext(
    sensor_id="mc",
    serial_number=115,
    utc_offset=0.0,
    date="20220602",
    location=custom_types.Location(
        location_id="ZEN",
        details="Zentralfriedhof",
        lon=16.438481,
        lat=48.147699,
        alt=180.0,
    ),
)


def get_dir_checksum(dirpath: str) -> str:
    return utils.run_shell_command("tar c src | md5sum")


@pytest.mark.integration
def test_pylot(wrap_test_with_mainlock):
    # TODO: remove old container artifacts
    # TODO: set up container
    # TODO: assert container copy equality
    # TODO: run container
    # TODO: assert output correctness
    pass
