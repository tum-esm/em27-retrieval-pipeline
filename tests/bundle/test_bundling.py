import os
import pytest
import tum_esm_utils
import src
import em27_metadata

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../..")
INPUT_DATA_DIR = os.path.join(PROJECT_DIR, "data", "testing", "inputs")
METADATA_DIR = os.path.join(INPUT_DATA_DIR, "metadata")

config = {
    "version":
        "1.4",
    "general": {
        "metadata": None,
        "data": {
            "ground_pressure": {
                "path": os.path.join(INPUT_DATA_DIR, "data", "log"),
                "file_regex": "^$(SENSOR_ID)$(DATE).*\\.csv$",
                "separator": ",",
                "pressure_column": "pressure",
                "pressure_column_format": "hPa",
                "date_column": "UTCdate_____",
                "date_column_format": "%Y-%m-%d",
                "time_column": "UTCtime_____",
                "time_column_format": "%H:%M:%S",
            },
            "atmospheric_profiles": os.path.join(INPUT_DATA_DIR, "data", "map"),
            "interferograms": os.path.join(INPUT_DATA_DIR, "data", "ifg"),
            "results": os.path.join(INPUT_DATA_DIR, "results"),
        },
    },
    "profiles":
        None,
    "retrieval":
        None,
    "bundles": [{
        "dst_dir": os.path.join(PROJECT_DIR, "data", "testing", "bundle", "outputs"),
        "output_formats": ["csv", "parquet"],
        "sensor_ids": ["so", "mc"],
        "retrieval_algorithms": ["proffast-1.0", "proffast-2.2", "proffast-2.3", "proffast-2.4"],
        "atmospheric_profile_models": ["GGG2014", "GGG2020"],
        "from_datetime": "2017-01-01T00:00:00+0000",
        "to_datetime": "2024-12-31T23:59:59+0000",
        "parse_dc_timeseries": True,
    }],
}


@pytest.mark.order(3)
@pytest.mark.quick
def test_bundling() -> None:
    src.bundle.main.run(
        config=src.types.Config.model_validate(config),
        em27_metadata_interface=em27_metadata.loader.load_from_local_files(
            locations_path=os.path.join(METADATA_DIR, "locations.json"),
            sensors_path=os.path.join(METADATA_DIR, "sensors.json"),
            campaigns_path=os.path.join(METADATA_DIR, "campaigns.json"),
        )
    )

    # TODO: Test existence of all bundles
    # TODO: test correct lengths/row counts of all bundles
    # TODO: test whether campaigns are correctly matched (only-so, etc.)
