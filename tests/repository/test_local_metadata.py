from typing import Generator
import os
import pytest
import tum_esm_utils
import src

CONFIG_DIR = tum_esm_utils.files.rel_to_abs_path("../../config")
LOCATIONS_PATH = os.path.join(CONFIG_DIR, "locations.json")
SENSORS_PATH = os.path.join(CONFIG_DIR, "sensors.json")
CAMPAIGNS_PATH = os.path.join(CONFIG_DIR, "campaigns.json")


@pytest.fixture(scope="function")
def store_local_metadata_during_test() -> Generator[None, None, None]:
    paths = [LOCATIONS_PATH, SENSORS_PATH, CAMPAIGNS_PATH]
    for path in paths:
        assert not os.path.isfile(path + ".tmp"), (
            "Temporary file already exists at: '" + path + ".tmp'"
        )

    for path in paths:
        if os.path.isfile(path):
            os.rename(path, path + ".tmp")

    yield

    for path in paths:
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isfile(path + ".tmp"):
            os.rename(path + ".tmp", path)


@pytest.mark.order(3)
@pytest.mark.quick
def test_local_metadata_loader(store_local_metadata_during_test: None) -> None:
    assert src.utils.metadata.load_local_em27_metadata_interface() is None

    with open(LOCATIONS_PATH, "w") as f:
        f.write("[]")

    with pytest.raises(FileNotFoundError):
        src.utils.metadata.load_local_em27_metadata_interface()

    with open(SENSORS_PATH, "w") as f:
        f.write("[]")

    with pytest.raises(FileNotFoundError):
        src.utils.metadata.load_local_em27_metadata_interface()

    with open(CAMPAIGNS_PATH, "w") as f:
        f.write("[]")

    interface = src.utils.metadata.load_local_em27_metadata_interface()
    assert interface is not None
    assert len(interface.locations.root) == 0
    assert len(interface.sensors.root) == 0
    assert len(interface.campaigns.root) == 0
