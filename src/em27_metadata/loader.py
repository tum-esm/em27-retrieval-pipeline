from typing import Optional
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

    # the metadata starting at pipeline v1.11 is stored in a single TOML file: em27_metadata.toml

    em27_metadata_object_string: Optional[str] = None
    try:
        em27_metadata_object_string = tum_esm_utils.code.request_github_file(
            repository=github_repository,
            filepath="em27_metadata.toml",
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
    # - data/locations.json
    # - data/sensors.json
    # - data/campaigns.json
    # - data/events.json

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
    locations_path: str,
    sensors_path: str,
    campaigns_path: Optional[str] = None,
    events_path: Optional[str] = None,
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

    with open(locations_path) as f:
        locations = em27_metadata_types.LocationMetadataList.model_validate_json(f.read())

    with open(sensors_path) as f:
        sensors = em27_metadata_types.SensorMetadataList.model_validate_json(f.read())

    campaigns = em27_metadata_types.CampaignMetadataList(root=[])
    if campaigns_path is not None:
        with open(campaigns_path) as f:
            campaigns = em27_metadata_types.CampaignMetadataList.model_validate_json(f.read())

    events = em27_metadata_types.EventMetadataList(root=[])
    if events_path is not None:
        with open(events_path) as f:
            events = em27_metadata_types.EventMetadataList.model_validate_json(f.read())

    return em27_metadata_interfaces.EM27MetadataInterface(
        locations=locations,
        sensors=sensors,
        campaigns=campaigns,
        events=events,
    )


def load_from_example_data() -> em27_metadata_interfaces.EM27MetadataInterface:
    _SAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
    return load_from_local_files(
        locations_path=os.path.join(_SAMPLE_DATA_DIR, "locations.json"),
        sensors_path=os.path.join(_SAMPLE_DATA_DIR, "sensors.json"),
        campaigns_path=os.path.join(_SAMPLE_DATA_DIR, "campaigns.json"),
        events_path=os.path.join(_SAMPLE_DATA_DIR, "events.json"),
    )
