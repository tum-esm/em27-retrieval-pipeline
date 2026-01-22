import datetime
import os
import pytest
import src
import tum_esm_utils
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
    "bundles": None,
    "geoms": {
        "sensor_ids": ["so", "mc"],
        "retrieval_algorithms": [
            "proffast-2.2",
            "proffast-2.3",
            "proffast-2.4",
            "proffast-2.4.1",
        ],
        "atmospheric_profile_models": ["GGG2014", "GGG2020"],
        "from_datetime": "2017-01-01T00:00:00+0000",
        "to_datetime": "2024-12-31T23:59:59+0000",
        "parse_dc_timeseries": True,
        "max_sza": 80,
        "min_xair": 0.98,
        "max_xair": 1.02,
        "conflict_mode": "replace",
    },
}

GEOMS_METADATA = {
    "general": {
        "network": "FTIR.COCCON",
        "affiliation": "TUM.ESM",
        "pressure_sensor_name": "young-61302",
    },
    "data": {
        "discipline": "ATMOSPHERIC.CHEMISTRY;REMOTE.SENSING;GROUNDBASED",
        "group": "EXPERIMENTAL;PROFILE.STATIONARY",
        "file_version": 2,
        "quality": "Station data.",
        "template": "GEOMS-TE-FTIR-COCCON-001",
    },
    "file": {
        "doi": "10.48477/COCCON.ITMS-B-FTIR.R01",
        "meta_version": "04R093;CUSTOM",
        "access": "COCCON",
        "project_id": "COCCON",
    },
    "principle_investigator": {
        "name": "Chen;Jia",
        "email": "jia.chen@tum.de",
        "affiliation": "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM",
        "address": "Theresienstr. 90;D-80333 Munich;GERMANY",
    },
    "data_originator": {
        "name": "Makowski;Moritz",
        "email": "moritz.makowski@tum.de",
        "affiliation": "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM",
        "address": "Theresienstr. 90;D-80333 Munich;GERMANY",
    },
    "data_submitter": {
        "name": "Dubravica;Darko",
        "email": "darko.dubravica@kit.edu",
        "affiliation": "Karlsruhe Institute of Technology;KIT",
        "address": "P.O. Box 3640;D-76021 Karlsruhe;GERMANY",
    },
    "locations": {
        "TUM_I": "MUNICH.TUM",
        "FEL": "MUNICH.FELDKIRCHEN",
        "GRAE": "MUNICH.GRAEFELFING",
        "OBE": "MUNICH.OBERSCHLEISSHEIM",
        "TAU": "MUNICH.TAUFKIRCHEN",
        "DLR": "MUNICH.DLR",
        "DLR_2": "MUNICH.DLR",
        "DLR_3": "MUNICH.DLR",
        "SOD": "SODANKYLA",
    },
}


@pytest.mark.order(3)
@pytest.mark.quick
def test_geoms_export(download_sample_data: None) -> None:
    # Remove all files in the output
    for f in tum_esm_utils.files.list_directory(
        BUNDLE_OUTPUT_DIR, include_directories=False, ignore=[".gitkeep"]
    ):
        os.remove(os.path.join(BUNDLE_OUTPUT_DIR, f))

    config = src.types.Config.model_validate(CONFIG)
    assert config.geoms is not None

    geoms_metadata = src.types.GEOMSMetadata.model_validate(GEOMS_METADATA)

    src.geoms.main.run(
        config=config,
        geoms_metadata=geoms_metadata,
        calibration_factors=src.types.CalibrationFactorsList(
            root=[
                src.types.CalibrationFactors(
                    sensor_id="so",
                    valid_from_datetime=datetime.datetime(2016, 1, 1).astimezone(
                        datetime.timezone.utc
                    ),
                    valid_to_datetime=datetime.datetime(2026, 1, 1).astimezone(
                        datetime.timezone.utc
                    ),
                    xco2=1.0,
                    xch4=1.0,
                    xh2o=1.0,
                    xco=1.0,
                ),
                src.types.CalibrationFactors(
                    sensor_id="mc",
                    valid_from_datetime=datetime.datetime(2016, 1, 1, tzinfo=datetime.timezone.utc),
                    valid_to_datetime=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
                    xco2=1.0,
                    xch4=1.0,
                    xh2o=1.0,
                    xco=1.0,
                ),
            ]
        ),
    )
