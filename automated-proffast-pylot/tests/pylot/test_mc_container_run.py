import pytest
import shutil
import os
from tests.fixtures import wrap_test_with_mainlock, PROJECT_DIR
from src import custom_types, utils, interfaces, procedures

CONTAINER_ROOT_DIR = os.path.join(PROJECT_DIR, "src", "prfpylot")
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
    return utils.run_shell_command(f"tar c {dirpath} | md5sum")


@pytest.mark.integration
def test_pylot(wrap_test_with_mainlock):
    # remove old containers
    for f in os.listdir(CONTAINER_ROOT_DIR):
        p = os.path.join(CONTAINER_ROOT_DIR, f)
        if os.path.isdir(p) and (p != "main"):
            shutil.rmtree(p)

    # set up container
    logger = utils.Logger("pytest", print_only=True)
    pylot_factory = interfaces.PylotFactory(logger)
    session = procedures.create_session.run(pylot_factory, SENSOR_DATA_CONTEXT)

    # assert container copy equality
    pylot_main_checksum = get_dir_checksum(os.path.join(CONTAINER_ROOT_DIR, "main"))
    pylot_copy_checksum = get_dir_checksum(session.container_path)
    assert pylot_main_checksum == pylot_copy_checksum

    # run container
    # TODO

    # assert output correctness
    # TODO
