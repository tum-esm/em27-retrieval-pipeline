# em27-metadata

`em27-metadata` provides validated schemas and query interfaces for EM27/SUN measurement metadata. Its source now lives in the [EM27 Retrieval Pipeline](https://github.com/tum-esm/em27-retrieval-pipeline) repository, while the library continues to be distributed under the `em27_metadata` package name. As of library version 1.11.0, the versioning of this library is in sync with the versioning of the EM27 Retrieval Pipeline.

```python
import datetime

import em27_metadata

metadata = em27_metadata.load_from_local_files(config_directory="config")
contexts = metadata.get(
    sensor_id="sensor-id",
    from_datetime=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    to_datetime=datetime.datetime(2026, 1, 1, 23, 59, 59, tzinfo=datetime.timezone.utc),
)
```

The loader supports the current `em27_metadata.toml` schema and the former `locations.json`, `sensors.json`, `campaigns.json`, and `events.json` layout. See the [metadata documentation](https://tum-esm.github.io/em27-retrieval-pipeline/guides/metadata) for configuration details.
