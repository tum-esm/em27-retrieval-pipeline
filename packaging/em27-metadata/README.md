# EM27 Metadata Library

`em27-metadata` provides validated schemas and query interfaces for EM27/SUN measurement metadata. Its source now lives in the [EM27 Retrieval Pipeline](https://github.com/tum-esm/em27-retrieval-pipeline) repository, while the library continues to be distributed under the `em27_metadata` package name. As of library version 1.11.0, the versioning of this library is in sync with the versioning of the EM27 Retrieval Pipeline.

The loader supports the current `em27_metadata.toml` schema and the former `locations.json`, `sensors.json`, `campaigns.json`, and `events.json` layout. See the [metadata documentation](https://tum-esm.github.io/em27-retrieval-pipeline/guides/em27-metadata) for configuration details.

## Library Usage

Install as a library:

```bash
pip install em27_metadata
# or
uv add em27_metadata
# or
pdm add em27_metadata
```

```python
import datetime
import em27_metadata

em27_metadata_store = em27_metadata.load_from_github(
    github_repository="org-name/repo-name",
    access_token="your github access token",
)

# or load it from local files
em27_metadata_store = em27_metadata.load_from_local_files(
    config_directory="directory that contains the em27_metadata.toml file",
)

metadata = location_data.get(
      sensor_id="sid1",
      from_datetime=datetime.datetime(
          2020, 8, 26, 0, 0, 0, tzinfo=datetime.timezone.utc
      ),
      to_datetime=datetime.datetime(
          2020, 8, 26, 23, 59, 59, tzinfo=datetime.timezone.utc
      ),
  )
  print(metadata)
```

Prints out something like this:

```json
[
  {
    "sensor_id": "sid1",
    "serial_number": 50,
    "from_datetime": "2020-08-26T00:00:00+0000",
    "to_datetime": "2020-08-26T23:59:59+0000",
    "location": {
      "location_id": "lid1",
      "details": "description of location 1",
      "lon": 10.5,
      "lat": 48.1,
      "alt": 500.0
    },
    "utc_offset": 2.0,
    "pressure_data_source": "LMU-MIM01-height-adjusted",
    "atmospheric_profile_location": {
      "location_id": "lid1",
      "details": "description of location 1",
      "lon": 10.5,
      "lat": 48.1,
      "alt": 500.0
    }
  }
]
```

The object returned by `em27_metadata_store.get()` is of type `list[em27_metadata.types.SensorDataContext]`. It is a Pydantic model (https://docs.pydantic.dev/) but can be converted to a dictionary using `metadata.model_dump()`.

The list will contain one item per time period where the metadata properties are continuous (same setup). You can find dummy data in the `data/` folder.
