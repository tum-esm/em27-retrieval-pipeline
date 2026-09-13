import os
import sys

import tomli_w


def _resolve_metadata_directory() -> str:
    configured_path = os.environ["EM27_METADATA_DIRECTORY"]
    if os.path.isabs(configured_path):
        return configured_path
    return os.path.abspath(os.path.join(os.environ["GITHUB_WORKSPACE"], configured_path))


def main() -> None:
    sys.path.insert(0, os.environ["EM27_METADATA_SOURCE_DIR"])
    import em27_metadata  # type: ignore

    metadata_directory = _resolve_metadata_directory()
    root_toml_path = os.path.join(metadata_directory, "em27_metadata.toml")
    data_directory = os.path.join(metadata_directory, "data")
    nested_toml_path = os.path.join(data_directory, "em27_metadata.toml")

    if os.path.isfile(root_toml_path):
        em27_metadata.load_from_local_files(config_directory=metadata_directory)
        print(f"Validated TOML metadata: {root_toml_path}")
        return

    if os.path.isfile(nested_toml_path):
        em27_metadata.load_from_local_files(config_directory=data_directory)
        print(f"Validated TOML metadata: {nested_toml_path}")
        return

    legacy_directory = (
        data_directory
        if os.path.isfile(os.path.join(data_directory, "locations.json"))
        else metadata_directory
    )
    locations_path = os.path.join(legacy_directory, "locations.json")
    sensors_path = os.path.join(legacy_directory, "sensors.json")
    if not os.path.isfile(locations_path) or not os.path.isfile(sensors_path):
        raise FileNotFoundError(
            "No EM27 metadata found. Expected em27_metadata.toml or legacy "
            "locations.json and sensors.json files (normally under data/)."
        )

    metadata = em27_metadata.load_from_local_files(
        locations_path=locations_path,
        sensors_path=sensors_path,
    )
    converted = em27_metadata.types.EM27MetadataObject(
        locations=metadata.locations,
        sensors=metadata.sensors,
        campaigns=metadata.campaigns,
        events=metadata.events,
    )

    print(f"Validated legacy JSON metadata in: {legacy_directory}")
    print("::group::Equivalent em27_metadata.toml")
    print(tomli_w.dumps(converted.model_dump(mode="json", exclude_none=True)).rstrip())
    print("::endgroup::")


if __name__ == "__main__":
    main()
