import datetime
import os
import pytest
import em27_metadata
import tum_esm_utils
from src import types
from tests.fixtures import (
    wrap_test_with_mainlock,
    download_sample_data,
    provide_config_template,
    clear_output_data,
)
from src import retrieval

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)

SENSOR_DATA_CONTEXTS = [
    em27_metadata.types.SensorDataContext(
        sensor_id="so",
        serial_number=39,
        from_datetime=datetime.datetime.combine(date, datetime.time.min),
        to_datetime=datetime.datetime.combine(date, datetime.time.max),
        utc_offset=0,
        pressure_data_source="so",
        calibration_factors=em27_metadata.types.CalibrationFactors(),
        multiple_ctx_on_this_date=False,
        location=em27_metadata.types.LocationMetadata(
            location_id="SOD",
            details="Sodankyla",
            lon=26.630,
            lat=67.366,
            alt=181.0,
        ),
    ) for date in [
        datetime.date(2017, 6, 8),
        datetime.date(2017, 6, 9),
    ]
] + [
    em27_metadata.types.SensorDataContext(
        sensor_id="mc",
        serial_number=115,
        from_datetime=datetime.datetime.combine(date, datetime.time.min),
        to_datetime=datetime.datetime.combine(date, datetime.time.max),
        utc_offset=0,
        pressure_data_source="mc",
        calibration_factors=em27_metadata.types.CalibrationFactors(),
        multiple_ctx_on_this_date=False,
        location=em27_metadata.types.LocationMetadata(
            location_id="ZEN",
            details="Zentralfriedhof",
            lon=16.438481,
            lat=48.147699,
            alt=180.0,
        ),
    ) for date in [
        datetime.date(2022, 6, 2),
    ]
]

TESTED_RETRIEVAL_ALGORITHMS: list[types.RetrievalAlgorithm] = [
    "proffast-1.0",
    "proffast-2.2",
    "proffast-2.3",
]
# TODO: test GGG2020 containers


@pytest.mark.order(2)
@pytest.mark.ci_intensive
def test_one_day(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    clear_output_data: None,
    provide_config_template: types.Config,
) -> None:
    _run_test_container(
        config=provide_config_template,
        sensor_data_contexts=[SENSOR_DATA_CONTEXTS[2]],
    )


@pytest.mark.order(3)
@pytest.mark.ci_complete
def test_three_days(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    clear_output_data: None,
    provide_config_template: types.Config,
) -> None:
    _run_test_container(
        config=provide_config_template,
        sensor_data_contexts=SENSOR_DATA_CONTEXTS,
    )


def _run_test_container(
    config: types.Config,
    sensor_data_contexts: list[em27_metadata.types.SensorDataContext],
) -> None:
    assert config.retrieval is not None

    # target config at test data
    config.general.data.datalogger.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "log"
    )
    config.general.data.interferograms.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "ifg"
    )
    config.general.data.atmospheric_profiles.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "map"
    )
    config.general.data.results.root = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "outputs"
    )

    for retrieval_algorithm in TESTED_RETRIEVAL_ALGORITHMS:
        # set up container factory
        logger = retrieval.utils.logger.Logger("pytest", print_only=True)
        container_factory = retrieval.dispatching.container_factory.ContainerFactory(
            config, logger
        )

        for sdc in sensor_data_contexts:
            # create session and run container
            session = retrieval.session.create_session.run(
                container_factory,
                sdc,
                retrieval_algorithm=retrieval_algorithm,
                atmospheric_profile_model="GGG2014",
            )
            retrieval.session.process_session.run(config, session)

            # assert output correctness
            date_string = sdc.from_datetime.strftime("%Y%m%d")
            out_path = os.path.join(
                PROJECT_DIR, "data/testing/container/outputs",
                retrieval_algorithm, "GGG2014", sdc.sensor_id, "successful",
                date_string
            )
            expected_files = [
                "about.json",
                "logfiles/container.log",
            ]
            if retrieval_algorithm in ["proffast-2.2", "proffast-2.3"]:
                expected_files.extend([
                    (
                        f"comb_invparms_{sdc.sensor_id}_SN{str(sdc.serial_number).zfill(3)}"
                        + f"_{date_string[2:]}-{date_string[2:]}.csv"
                    ),
                    "pylot_config.yml",
                    "pylot_log_format.yml",
                    "logfiles/preprocess_output.log",
                    "logfiles/pcxs_output.log",
                    "logfiles/inv_output.log",
                ])
            if retrieval_algorithm == "proffast-1.0":
                expected_files.extend([
                    (f"{sdc.sensor_id}{date_string[2:]}-combined-invparms.csv"),
                    (
                        f"{sdc.sensor_id}{date_string[2:]}-combined-invparms.parquet"
                    ),
                    "logfiles/wrapper.log",
                    "logfiles/preprocess4.log",
                    "logfiles/pcxs10.log",
                    "logfiles/invers10.log",
                ])

            for filename in expected_files:
                filepath = os.path.join(out_path, filename)
                assert os.path.isfile(
                    filepath
                ), f"output file does not exist ({filepath})"
