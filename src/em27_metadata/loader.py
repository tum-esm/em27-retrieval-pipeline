from typing import Literal, Optional
import tum_esm_utils
import tomllib
import os
from . import interfaces as em27_metadata_interfaces
from . import types as em27_metadata_types


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
            tomllib.loads(em27_metadata_object_string)
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

    # the metadata starting at pipeline v1.11 is stored in a single TOML file: em27_metadata.toml
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
        p = os.path.join(config_directory, "em27_metadata.toml")
        if os.path.isfile(p):
            em27_metadata_object = em27_metadata_types.EM27MetadataObject.model_validate(
                tum_esm_utils.files.load_toml_file(p)
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

    return em27_metadata_interfaces.EM27MetadataInterface(
        locations=locations,
        sensors=sensors,
        campaigns=campaigns,
        events=events,
    )


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
