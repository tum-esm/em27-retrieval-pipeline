from pathlib import PosixPath
from typing import Optional, Union
import os
import yaml
import em27_metadata
import tum_esm_utils


def read_yaml(
        file_path: Union[str, PosixPath]
) -> dict[str, str]:
    with open(file_path, 'r') as f:
        return dict(yaml.load(f, Loader=yaml.FullLoader))


config_setup = read_yaml(tum_esm_utils.files.rel_to_abs_path("../../config_setup.yml"))
if config_setup['alternate_config_dir'] is None:
    CONFIG_DIR = tum_esm_utils.files.rel_to_abs_path("../../config")
else:
    CONFIG_DIR = config_setup['alternate_config_dir']
print("CONFIG DIR: ", CONFIG_DIR)


def load_local_em27_metadata_interface(
) -> Optional[em27_metadata.EM27MetadataInterface]:
    assert os.path.isdir(CONFIG_DIR)
    locations_path = os.path.join(CONFIG_DIR, "locations.json")
    sensors_path = os.path.join(CONFIG_DIR, "sensors.json")
    campaigns_path = os.path.join(CONFIG_DIR, "campaigns.json")
    file_existence = [
        os.path.isfile(locations_path),
        os.path.isfile(sensors_path),
        os.path.isfile(campaigns_path),
    ]
    if any(file_existence):
        if not all(file_existence):
            raise FileNotFoundError(
                "Found some local metadata files but not all (loca" +
                "tions.json, sensors.json, campaigns.json). Please " +
                "add or remove all local metadata files."
            )
        return em27_metadata.loader.load_from_local_files(
            locations_path, sensors_path, campaigns_path
        )
    else:
        return None
