# Validate EM27 metadata

This composite action validates metadata-storage repositories against the schemas bundled with the EM27 Retrieval Pipeline. It accepts either:

- `em27_metadata.toml` in the repository root (preferred), or
- the legacy `data/locations.json`, `data/sensors.json`, `data/campaigns.json`, and optional `data/events.json` layout.

Legacy JSON metadata is also printed as equivalent TOML in the workflow log.

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: tum-esm/em27-retrieval-pipeline/.github/actions/validate-metadata@v1.11.1
```

For metadata in a subdirectory, pass `metadata-directory`:

```yaml
  - uses: tum-esm/em27-retrieval-pipeline/.github/actions/validate-metadata@v1.11.1
    with:
      metadata-directory: path/to/metadata
```
