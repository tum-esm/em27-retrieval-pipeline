import os
import pytest
import src
import tum_esm_utils
import em27_metadata
import polars as pl
from ..fixtures import download_sample_data

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../..")
INPUT_DATA_DIR = os.path.join(PROJECT_DIR, "data", "testing", "inputs")
METADATA_DIR = os.path.join(INPUT_DATA_DIR, "metadata")
BUNDLE_OUTPUT_DIR = os.path.join(PROJECT_DIR, "data", "testing", "bundle", "outputs")

CONFIG = {
    "version": "1.6",
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
    "profiles": None,
    "retrieval": None,
    "bundles": [
        {
            "dst_dir": BUNDLE_OUTPUT_DIR,
            "output_formats": ["csv", "parquet"],
            "sensor_ids": ["so", "mc"],
            "retrieval_algorithms": [
                "proffast-1.0",
                "proffast-2.2",
                "proffast-2.3",
                "proffast-2.4",
            ],
            "atmospheric_profile_models": ["GGG2014", "GGG2020"],
            "from_datetime": "2017-01-01T00:00:00+0000",
            "to_datetime": "2024-12-31T23:59:59+0000",
            "parse_dc_timeseries": True,
        }
    ],
}


@pytest.mark.order(3)
@pytest.mark.quick
def test_bundling(download_sample_data: None) -> None:
    # Remove all files in the output
    for f in tum_esm_utils.files.list_directory(
        BUNDLE_OUTPUT_DIR, include_directories=False, ignore=[".gitkeep"]
    ):
        os.remove(os.path.join(BUNDLE_OUTPUT_DIR, f))

    config = src.types.Config.model_validate(CONFIG)
    assert config.bundles is not None

    src.bundle.main.run(
        config=config,
        em27_metadata_interface=em27_metadata.loader.load_from_local_files(
            locations_path=os.path.join(METADATA_DIR, "locations.json"),
            sensors_path=os.path.join(METADATA_DIR, "sensors.json"),
            campaigns_path=os.path.join(METADATA_DIR, "campaigns.json"),
        ),
    )

    bundle = config.bundles[0]
    min_row_counts = {"mc": 8, "so": 15}

    for sensor_id in bundle.sensor_ids:
        for retrieval_algorithm in bundle.retrieval_algorithms:
            for atmospheric_profile_model in bundle.atmospheric_profile_models:
                if retrieval_algorithm == "proffast-1.0" and atmospheric_profile_model == "GGG2020":
                    continue

                filename = "-".join(
                    [
                        "em27-retrieval-bundle",
                        sensor_id,
                        retrieval_algorithm,
                        atmospheric_profile_model,
                        bundle.from_datetime.strftime("%Y%m%d"),
                        bundle.to_datetime.strftime("%Y%m%d"),
                    ]
                )
                # fmt: off
                csv_path = os.path.join(BUNDLE_OUTPUT_DIR, f"{filename}.csv")
                assert os.path.exists(csv_path), f"Expected file {csv_path} does not exist."
                csv_df = pl.read_csv(csv_path)
                with pl.Config(tbl_cols=-1):
                    print(csv_df)
                assert len(csv_df) >= min_row_counts[sensor_id], \
                    f"Expected at least {min_row_counts[sensor_id]} rows in {csv_path}, got {len(csv_df)}."

                parquet_path = os.path.join(BUNDLE_OUTPUT_DIR, f"{filename}.parquet")
                assert os.path.exists(parquet_path), f"Expected file {parquet_path} does not exist."
                parquet_df = pl.read_parquet(parquet_path)
                with pl.Config(tbl_cols=-1):
                    print(parquet_df)
                assert len(parquet_df) >= min_row_counts[sensor_id], \
                    f"Expected at least {min_row_counts[sensor_id]} rows in {parquet_path}, got {len(parquet_df)}."

                campaigns: set[str] = set()
                for c in parquet_df["campaign_ids"]:
                    for c in c.split("+"):
                        campaigns.add(c)

                assert "both" in campaigns, f"Expected 'both' in campaigns, got {campaigns}."
                assert "none" not in campaigns, f"Expected 'none' not in campaigns, got {campaigns}."
                assert f"only-{sensor_id}" in campaigns, f"Expected 'only-{sensor_id}' in campaigns, got {campaigns}."
                assert len(campaigns) == 2, f"Expected 2 campaigns, got {len(campaigns)}."
