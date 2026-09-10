import os
from typing import Optional
from src import types, em27_metadata


def load_local_em27_metadata_interface(
    config_dir: str = types.Config.get_config_dir(),
) -> Optional[em27_metadata.EM27MetadataInterface]:
    config_dir = os.path.abspath(config_dir)
    if not os.path.isdir(config_dir):
        return None

    # TODO: refactor this loading

    toml_path = os.path.join(config_dir, "em27_metadata.toml")
    if os.path.isfile(toml_path):
        return em27_metadata.loader.load_from_local_files(config_directory=config_dir)

    locations_path = os.path.join(config_dir, "locations.json")
    sensors_path = os.path.join(config_dir, "sensors.json")
    campaigns_path = os.path.join(config_dir, "campaigns.json")
    events_path = os.path.join(config_dir, "events.json")
    file_existence = [
        os.path.isfile(locations_path),
        os.path.isfile(sensors_path),
    ]
    if any(file_existence):
        if not all(file_existence):
            raise FileNotFoundError(
                "Found some local metadata files but not all (loca"
                + "tions.json, sensors.json). Please "
                + "add or remove all local metadata files."
            )
        return em27_metadata.loader.load_from_local_files(config_directory=config_dir)
    else:
        return None
