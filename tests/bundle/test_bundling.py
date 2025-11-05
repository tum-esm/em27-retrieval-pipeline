import datetime
import os
import pytest
import src
import tum_esm_utils
import em27_metadata
import polars as pl
from ..fixtures import download_sample_data  # pyright: ignore[reportUnusedImport]

PROJECT_DIR = tum_esm_utils.files.rel_to_abs_path("../..")
INPUT_DATA_DIR = os.path.join(PROJECT_DIR, "data", "testing", "inputs")
METADATA_DIR = os.path.join(INPUT_DATA_DIR, "metadata")
BUNDLE_OUTPUT_DIR = os.path.join(PROJECT_DIR, "data", "testing", "bundle", "outputs")

CONFIG = {
    "version": "1.9",
    "general": {
        "metadata": None,
        "data": {
            "ground_pressure": {
                "path": os.path.join(INPUT_DATA_DIR, "data", "ground-pressure"),
                "file_regex": "^$(SENSOR_ID)$(DATE).*\\.csv$",
                "separator": ",",
                "pressure_column": "pressure",
                "pressure_column_format": "hPa",
                "date_column": "UTCdate_____",
                "date_column_format": "%Y-%m-%d",
                "time_column": "UTCtime_____",
                "time_column_format": "%H:%M:%S",
            },
            "atmospheric_profiles": os.path.join(INPUT_DATA_DIR, "data", "atmospheric-profiles"),
            "interferograms": os.path.join(INPUT_DATA_DIR, "data", "interferograms"),
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
                "proffast-2.4.1",
            ],
            "atmospheric_profile_models": ["GGG2014", "GGG2020"],
            "from_datetime": "2017-01-01T00:00:00+0000",
            "to_datetime": "2024-12-31T23:59:59+0000",
            "parse_dc_timeseries": True,
            "parse_retrieval_diagnostics": True,
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
            events_path=os.path.join(METADATA_DIR, "events.json"),
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

                df = parquet_df.drop_nulls().drop_nans()
                assert len(df) == len(parquet_df), f"Expected no nulls or NaNs in the DataFrame"

                print(df.columns)

                # check whether DC timeseries is there
                if retrieval_algorithm in ["proffast-2.4", "proffast-2.4.1"]:
                    for ch in ["ch1", "ch2"]:
                        for direction in ["fwd", "bwd"]:
                            for var in ["min", "max", "mean", "var"]:
                                col = f"{ch}_{direction}_dc_{var}"
                                if col not in df.columns:
                                    raise Exception(f"Column {col} missing in DataFrame columns:")

                # check whether opus file stats are there
                if retrieval_algorithm != "proffast-1.0":
                    for c in [
                        'ABP', 'LWN', 'RSN', 'TSC', 'DUR', 'MVD', 'PKA', 'PKL', 'PRA', 'PRL', 'P2A', 'P2L', 'P2R', 'P2K'
                    ]:
                        col = f"instrument_{c}"
                        if col not in df.columns:
                            raise Exception(f"Column {col} missing in DataFrame columns:")

                # check whether retrieval diagnostics are there
                for gas in ["CO2", "CH4", "H2O", "CO"]:
                    for suffix in ["niter", "rms", "scl"]:
                        col = f"{gas}_{suffix}"
                        if col not in df.columns:
                            raise Exception(f"Column {col} missing in DataFrame columns:")

                # test event columns
                for c in ["event_description", "event_data_quality_flag"]:
                    assert c in df.columns, f"Column {c} missing in DataFrame columns."

                # quality flag all 0 for sensor "mc"
                # quality flag all 0 for sensor "so" and date 9
                # quality flag all 1 for sensor "so" and date 8
                if sensor_id == "mc":
                    assert all(df["event_description"].eq("")), "Expected all event descriptions to be empty for sensor 'mc'."
                    assert all(df["event_data_quality_flag"].eq(0)), "Expected all quality flags to be 0 for sensor 'mc'."
                elif sensor_id == "so":
                    date_8_df = df.filter(pl.col("utc").dt.date().eq(datetime.date(2017,6,8)))
                    assert all(
                        date_8_df["event_description"].eq("test event")
                    ), "Expected all event descriptions to be 'test event' for sensor 'so' on day 8."
                    assert all(
                        date_8_df["event_data_quality_flag"].eq(1)
                    ), "Expected all quality flags to be 1 for sensor 'so' on day 8."

                    date_9_df = df.filter(pl.col("utc").dt.date().eq(datetime.date(2017,6,9)))
                    assert all(
                        date_9_df["event_description"].eq("")
                    ), "Expected all event descriptions to be empty for sensor 'so' on day 9."
                    assert all(
                        date_9_df["event_data_quality_flag"].eq(0)
                    ), "Expected all quality flags to be 0 for sensor 'so' on day 9."
