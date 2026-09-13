import os
from typing import Callable, Literal, Optional

import tomli
import tum_esm_utils

from . import interfaces as em27_metadata_interfaces
from . import types as em27_metadata_types


def load_from_config(
    source: Literal["local", "github"],
    github_repository: Optional[str],
    github_access_token: Optional[str],
    config_directory: str,
    log: Optional[Callable[[str], None]] = None,
) -> em27_metadata_interfaces.EM27MetadataInterface:
    """Load metadata from the configured local or GitHub source.

    Args:
        source: Where to load the metadata from.
        github_repository: GitHub repository in ``owner/repository`` format.
        github_access_token: Optional token for a private GitHub repository.
        log: Optional function receiving progress messages.
        config_directory: Directory containing local metadata files.
    """

    if source == "local":
        if log is not None:
            log(f"Loading metadata from local directory: {config_directory}")
        metadata = load_from_local_files(config_directory=config_directory)
        if log is not None:
            log("Successfully loaded local metadata")
        return metadata

    elif source == "github":
        if github_repository is None:
            raise ValueError("github_repository is required when metadata source is 'github'")

        if log is not None:
            log(f"Loading metadata from GitHub repository: {github_repository}")
        metadata = load_from_github(
            github_repository=github_repository,
            access_token=github_access_token,
        )
        if log is not None:
            log("Successfully loaded metadata from GitHub")
        return metadata

    raise ValueError(f"Unknown metadata source: {source}")


def load_from_github(
    github_repository: str,
    access_token: Optional[str] = None,
) -> em27_metadata_interfaces.EM27MetadataInterface:
    """Loads an EM27MetadataInterface from GitHub

    Args:
        github_repository:  The repository to load the metadata from, e.g. passing
                            "em27/em27-metadata" would mean that the repository is
                            hosted at `github.com/em27/em27-metadata`.
        access_token:       The access token to use for the request. This is only
                            required if the GitHub repository is private. You can
                            read about these tokens at https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens.

    Returns:  An metadata object containing all the metadata that can now be queried
              locally using `metadata.get`.

    Raises:
        requests.exceptions.HTTPError:  If the request to GitHub fails.
        pydantic.ValidationError:       If the response is not in a valid format.
    """

    # the metadata starting at pipeline v1.11 is stored in a single TOML file: em27_metadata.toml (now it is no longer expected to be in the data/ subdirectory)

    em27_metadata_object_string: Optional[str] = None
    try:
        em27_metadata_object_string = tum_esm_utils.code.request_github_file(
            repository=github_repository,
            filepath="em27_metadata.toml",
            access_token=access_token,
        )
    except Exception:
        pass
    # keep the old path in case people forget to put it in the root directory of the repository
    if em27_metadata_object_string is None:
        try:
            em27_metadata_object_string = tum_esm_utils.code.request_github_file(
                repository=github_repository,
                filepath="data/em27_metadata.toml",
                access_token=access_token,
            )
        except Exception:
            pass
    if em27_metadata_object_string is not None:
        em27_metadata_object = em27_metadata_types.EM27MetadataObject.model_validate(
            tomli.loads(em27_metadata_object_string)
        )
        return em27_metadata_interfaces.EM27MetadataInterface(
            locations=em27_metadata_object.locations,
            sensors=em27_metadata_object.sensors,
            campaigns=em27_metadata_object.campaigns,
            events=em27_metadata_object.events,
        )

    # the metadata until pipeline v1.10 was stored in separate JSON files:
    # - locations.json
    # - sensors.json
    # - campaigns.json
    # - events.json

    locations = em27_metadata_types.LocationMetadataList.model_validate_json(
        tum_esm_utils.code.request_github_file(
            repository=github_repository,
            filepath="data/locations.json",
            access_token=access_token,
        )
    )

    sensors = em27_metadata_types.SensorMetadataList.model_validate_json(
        tum_esm_utils.code.request_github_file(
            repository=github_repository,
            filepath="data/sensors.json",
            access_token=access_token,
        )
    )

    campaigns = em27_metadata_types.CampaignMetadataList.model_validate_json(
        tum_esm_utils.code.request_github_file(
            repository=github_repository,
            filepath="data/campaigns.json",
            access_token=access_token,
        )
    )

    events = em27_metadata_types.EventMetadataList(root=[])
    try:
        events = em27_metadata_types.EventMetadataList.model_validate_json(
            tum_esm_utils.code.request_github_file(
                repository=github_repository,
                filepath="data/events.json",
                access_token=access_token,
            )
        )
    except Exception:
        pass

    return em27_metadata_interfaces.EM27MetadataInterface(
        locations=locations,
        sensors=sensors,
        campaigns=campaigns,
        events=events,
    )


def load_from_local_files(
    locations_path: Optional[str] = None,
    sensors_path: Optional[str] = None,
    campaigns_path: Optional[str] = None,
    events_path: Optional[str] = None,
    config_directory: Optional[str] = None,
    template: bool = False,
) -> em27_metadata_interfaces.EM27MetadataInterface:
    """Loads an EM27MetadataInterface from local files.

    Args:
        locations_path:  path to the locations file, e.g. "data/locations.json"
        sensors_path:    path to the sensors file, e.g. "data/sensors.json"
        campaigns_path:  path to the campaigns file, e.g. "data/campaigns.json" not
                         required for the profile download and the retrieval in the
                         EM27 Retrieval Pipeline

    Returns:  An metadata object containing all the metadata that can now be queried
              locally using `metadata.get`.

    Raises:
        FileNotFoundError:              If a file does not exist.
        pydantic.ValidationError:       If a file is not in a valid format.
    """

    if config_directory is not None:
        config_directory = os.path.abspath(config_directory)
    if locations_path is not None:
        locations_path = os.path.abspath(locations_path)
    if sensors_path is not None:
        sensors_path = os.path.abspath(sensors_path)
    if campaigns_path is not None:
        campaigns_path = os.path.abspath(campaigns_path)
    if events_path is not None:
        events_path = os.path.abspath(events_path)

    # the metadata starting at pipeline v1.11 is stored in a single TOML file: em27_metadata.toml
    toml_path: Optional[str] = None
    if config_directory is not None:
        assert locations_path is None, (
            "locations_path should not be provided when config_directory is provided"
        )
        assert sensors_path is None, (
            "sensors_path should not be provided when config_directory is provided"
        )
        assert campaigns_path is None, (
            "campaigns_path should not be provided when config_directory is provided"
        )
        assert events_path is None, (
            "events_path should not be provided when config_directory is provided"
        )

        # try to load the em27_metadata.toml file from the config directory
        toml_path = os.path.join(
            config_directory, f"em27_metadata.{'template.' if template else ''}toml"
        )
        if os.path.isfile(toml_path):
            with open(toml_path, "rb") as file:
                toml_data = tomli.load(file)
            em27_metadata_object = em27_metadata_types.EM27MetadataObject.model_validate(toml_data)
            return em27_metadata_interfaces.EM27MetadataInterface(
                locations=em27_metadata_object.locations,
                sensors=em27_metadata_object.sensors,
                campaigns=em27_metadata_object.campaigns,
                events=em27_metadata_object.events,
            )

    # the metadata until pipeline v1.10 was stored in separate JSON files:
    # - locations.json
    # - sensors.json
    # - campaigns.json
    # - events.json

    if config_directory is not None:
        locations_path = os.path.join(config_directory, "locations.json")
        sensors_path = os.path.join(config_directory, "sensors.json")
        campaigns_path = os.path.join(config_directory, "campaigns.json")
        events_path = os.path.join(config_directory, "events.json")
    else:
        # same logic as before -> locations and sensors path must be provided, campaigns and events are optional
        assert locations_path is not None, (
            "locations_path must be provided when config_directory is not provided"
        )
        assert sensors_path is not None, (
            "sensors_path must be provided when config_directory is not provided"
        )
        if campaigns_path is None:
            campaigns_path = os.path.join(os.path.dirname(locations_path), "campaigns.json")
        if events_path is None:
            events_path = os.path.join(os.path.dirname(locations_path), "events.json")

    locations = em27_metadata_types.LocationMetadataList.model_validate_json(
        tum_esm_utils.files.load_file(locations_path)
    )
    sensors = em27_metadata_types.SensorMetadataList.model_validate_json(
        tum_esm_utils.files.load_file(sensors_path)
    )

    campaigns = em27_metadata_types.CampaignMetadataList(root=[])
    try:
        campaigns = em27_metadata_types.CampaignMetadataList.model_validate_json(
            tum_esm_utils.files.load_file(campaigns_path)
        )
    except FileNotFoundError:
        pass

    events = em27_metadata_types.EventMetadataList(root=[])
    try:
        events = em27_metadata_types.EventMetadataList.model_validate_json(
            tum_esm_utils.files.load_file(events_path)
        )
    except FileNotFoundError:
        pass

    em27_metadata_interface = em27_metadata_interfaces.EM27MetadataInterface(
        locations=locations,
        sensors=sensors,
        campaigns=campaigns,
        events=events,
    )

    if (toml_path is not None) and (not os.path.isfile(toml_path)):
        em27_metadata_object = em27_metadata_types.EM27MetadataObject(
            locations=locations,
            sensors=sensors,
            campaigns=campaigns,
            events=events,
        )
        tmp_toml_path = toml_path.removesuffix(".toml") + ".tmp.toml"
        tum_esm_utils.files.dump_toml_file(
            tmp_toml_path,
            em27_metadata_object.model_dump(mode="json", exclude_none=True),
        )
        os.replace(tmp_toml_path, toml_path)

    return em27_metadata_interface


def load_from_example_data(
    variant: Literal["toml", "json", "fallbacktest1", "fallbacktest2"] = "toml",
) -> em27_metadata_interfaces.EM27MetadataInterface:
    _SAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
    if variant == "toml":
        return load_from_local_files(
            config_directory=os.path.join(_SAMPLE_DATA_DIR, "toml"),
        )
    elif variant == "json":
        return load_from_local_files(
            locations_path=os.path.join(_SAMPLE_DATA_DIR, "json", "locations.json"),
            sensors_path=os.path.join(_SAMPLE_DATA_DIR, "json", "sensors.json"),
            campaigns_path=os.path.join(_SAMPLE_DATA_DIR, "json", "campaigns.json"),
            events_path=os.path.join(_SAMPLE_DATA_DIR, "json", "events.json"),
        )
    elif variant == "fallbacktest1":
        return load_from_local_files(
            locations_path=os.path.join(_SAMPLE_DATA_DIR, "json", "locations.json"),
            sensors_path=os.path.join(_SAMPLE_DATA_DIR, "json", "sensors.json"),
        )
    elif variant == "fallbacktest2":
        return load_from_local_files(
            config_directory=os.path.join(_SAMPLE_DATA_DIR, "json"),
        )
