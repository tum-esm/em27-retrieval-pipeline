import os
from typing import Optional

import em27_metadata

from src import types


def load_local_em27_metadata_interface(
    config_dir: str = types.Config.get_config_dir(),
) -> Optional[em27_metadata.EM27MetadataInterface]:
    if not os.path.isdir(config_dir):
        return None
    locations_path = os.path.join(config_dir, "locations.json")
    sensors_path = os.path.join(config_dir, "sensors.json")
    campaigns_path = os.path.join(config_dir, "campaigns.json")
    file_existence = [
        os.path.isfile(locations_path),
        os.path.isfile(sensors_path),
        os.path.isfile(campaigns_path),
    ]
    if any(file_existence):
        if not all(file_existence):
            raise FileNotFoundError(
                "Found some local metadata files but not all (loca"
                + "tions.json, sensors.json, campaigns.json). Please "
                + "add or remove all local metadata files."
            )
        return em27_metadata.loader.load_from_local_files(
            locations_path, sensors_path, campaigns_path
        )
    else:
        return None
