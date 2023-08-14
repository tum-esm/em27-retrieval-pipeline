import datetime
import os
from typing import Literal
import pytest
import tum_esm_em27_metadata
import tum_esm_utils
from tests.fixtures import (
    wrap_test_with_mainlock,
    download_sample_data,
    provide_config_template,
    clear_output_data,
)
from src import custom_types, utils, interfaces, procedures

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)

SENSOR_DATA_CONTEXTS = [
    tum_esm_em27_metadata.types.SensorDataContext(
        sensor_id="so",
        serial_number=39,
        from_datetime=datetime.datetime.fromisoformat(date + "T00:00:00+00:00"),
        to_datetime=datetime.datetime.fromisoformat(date + "T23:59:59+00:00"),
        utc_offset=0,
        pressure_data_source="so",
        pressure_calibration_factor=1,
        output_calibration_factors_xco2=[],
        output_calibration_factors_xch4=[],
        output_calibration_factors_xco=[],
        output_calibration_scheme=None,
        multiple_ctx_on_this_date=False,
        location=tum_esm_em27_metadata.types.LocationMetadata(
            location_id="SOD",
            details="Sodankyla",
            lon=26.630,
            lat=67.366,
            alt=181.0,
        ),
    )
    for date in ["2017-06-08", "2017-06-09"]
] + [
    tum_esm_em27_metadata.types.SensorDataContext(
        sensor_id="mc",
        serial_number=115,
        from_datetime=datetime.datetime.fromisoformat(date + "T00:00:00+00:00"),
        to_datetime=datetime.datetime.fromisoformat(date + "T23:59:59+00:00"),
        utc_offset=0,
        pressure_data_source="mc",
        pressure_calibration_factor=1,
        output_calibration_factors_xco2=[],
        output_calibration_factors_xch4=[],
        output_calibration_factors_xco=[],
        output_calibration_scheme=None,
        multiple_ctx_on_this_date=False,
        location=tum_esm_em27_metadata.types.LocationMetadata(
            location_id="ZEN",
            details="Zentralfriedhof",
            lon=16.438481,
            lat=48.147699,
            alt=180.0,
        ),
    )
    for date in ["2022-06-02"]
]

# SENSOR_DATA_CONTEXTS = SENSOR_DATA_CONTEXTS[2:]
TESTED_PROFFAST_VERSIONS: list[Literal["proffast-1.0", "proffast-2.2"]] = [
    "proffast-1.0",
    "proffast-2.2",
]


@pytest.mark.integration
def test_container(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    clear_output_data: None,
    provide_config_template: custom_types.Config,
) -> None:
    config = provide_config_template
    assert config.automated_proffast is not None

    # target config at test data
    config.automated_proffast.data_filter.sensor_ids_to_consider = ["mc", "so"]
    config.automated_proffast.data_filter.from_date = datetime.date(2017, 6, 8)
    config.automated_proffast.data_filter.to_date = datetime.date(2022, 6, 2)
    config.general.data_src_dirs.datalogger = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "log"
    )
    config.general.data_src_dirs.interferograms = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "ifg"
    )
    config.general.data_src_dirs.vertical_profiles = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "map"
    )
    config.general.data_dst_dirs.results = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "outputs"
    )

    for proffast_version in TESTED_PROFFAST_VERSIONS:
        config.automated_proffast.general.retrieval_software = proffast_version

        # set up container factory
        logger = utils.proffast.Logger("pytest", print_only=True)
        container_factory = interfaces.proffast.ContainerFactory(config, logger)

        for sdc in SENSOR_DATA_CONTEXTS:
            # create session and run container
            session = procedures.proffast.create_session.run(container_factory, sdc)
            procedures.proffast.process_session.run(config, session)

            # assert output correctness
            date_string = sdc.from_datetime.strftime("%Y%m%d")
            out_path = os.path.join(
                PROJECT_DIR,
                "data/testing/container/outputs",
                sdc.sensor_id,
                f"{proffast_version}-outputs/successful",
                date_string,
            )
            expected_files = [
                "about.json",
                "logfiles/container.log",
            ]
            if proffast_version == "proffast-2.2":
                expected_files = [
                    (
                        f"comb_invparms_{sdc.sensor_id}_SN{str(sdc.serial_number).zfill(3)}"
                        + f"_{date_string[2:]}-{date_string[2:]}.csv"
                    ),
                    "pylot_config.yml",
                    "pylot_log_format.yml",
                    "logfiles/preprocess_output.log",
                    "logfiles/pcxs_output.log",
                    "logfiles/inv_output.log",
                ]
            else:
                expected_files = [
                    (f"{sdc.sensor_id}{date_string[2:]}-combined-invparms.csv"),
                    (f"{sdc.sensor_id}{date_string[2:]}-combined-invparms.parquet"),
                    "logfiles/wrapper.log",
                    "logfiles/preprocess4.log",
                    "logfiles/pcxs10.log",
                    "logfiles/invers10.log",
                ]

            for filename in expected_files:
                filepath = os.path.join(out_path, filename)
                assert os.path.isfile(
                    filepath
                ), f"output file does not exist ({filepath})"
