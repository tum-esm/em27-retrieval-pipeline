from typing import Generator
import datetime
import os
import time
import pytest
import em27_metadata
import tum_esm_utils
import multiprocessing
import src
from tests.fixtures import (
    wrap_test_with_mainlock, download_sample_data, provide_config_template,
    remove_temporary_retrieval_data
)

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
        atmospheric_profile_location=em27_metadata.types.LocationMetadata(
            location_id="SOD",
            details="Sodankyla",
            lon=26.630,
            lat=67.366,
            alt=181.0,
        ),
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
        atmospheric_profile_location=em27_metadata.types.LocationMetadata(
            location_id="ZEN",
            details="Zentralfriedhof",
            lon=16.438481,
            lat=48.147699,
            alt=180.0,
        ),
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


@pytest.fixture(scope="session")
def provide_container_factory(
    provide_config_template: src.types.Config,
) -> Generator[src.retrieval.dispatching.container_factory.ContainerFactory,
               None, None]:
    logger = src.retrieval.utils.logger.Logger(
        "pytest",
        write_to_file=False,
        print_to_console=True,
    )
    yield src.retrieval.dispatching.container_factory.ContainerFactory(
        provide_config_template, logger, test_mode=True
    )


@pytest.mark.order(3)
@pytest.mark.quick
def test_sdc_covers_the_full_day() -> None:
    for sdc in SENSOR_DATA_CONTEXTS:
        assert src.utils.functions.sdc_covers_the_full_day(sdc)


# this test will only mock the retrieval algorithm
@pytest.mark.order(4)
@pytest.mark.ci
def test_container_lifecycle_ci(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    remove_temporary_retrieval_data: None,
    provide_config_template: src.types.Config,
    provide_container_factory: src.retrieval.dispatching.container_factory.
    ContainerFactory,
) -> None:
    _run(
        provide_config_template,
        provide_container_factory,
        only_run_mock_retrieval=True,
    )


# this test will run the actual retrieval algorithm
@pytest.mark.order(5)
@pytest.mark.complete
def test_container_lifecycle_complete(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    remove_temporary_retrieval_data: None,
    provide_config_template: src.types.Config,
    provide_container_factory: src.retrieval.dispatching.container_factory.
    ContainerFactory,
) -> None:
    _run(
        provide_config_template,
        provide_container_factory,
        only_run_mock_retrieval=False,
    )


def run_session(
    session: src.types.RetrievalSession, config: src.types.Config,
    only_run_mock_retrieval: bool
) -> None:
    src.retrieval.session.process_session.run(
        config,
        session,
        test_mode=only_run_mock_retrieval,
    )
    _assert_output_correctness(
        session.retrieval_algorithm,
        session.atmospheric_profile_model,
        session.ctx,
    )


def _run(
    config: src.types.Config,
    container_factory: src.retrieval.dispatching.container_factory.
    ContainerFactory,
    only_run_mock_retrieval: bool,
) -> None:
    _point_config_to_test_data(config)
    src.retrieval.utils.retrieval_status.RetrievalStatusList.reset()
    assert config.retrieval is not None

    NUMBER_OF_JOBS = len(SENSOR_DATA_CONTEXTS) * 2 * 3
    print(f"Running {NUMBER_OF_JOBS} retrieval jobs in parallel")

    atm: src.types.AtmosphericProfileModel
    alg: src.types.RetrievalAlgorithm
    pending_processes: list[multiprocessing.Process] = []

    # start proffast 1.0 first because it takes the longest
    for alg in [ # type: ignore
        "proffast-1.0", "proffast-2.2", "proffast-2.3"
    ]:
        for atm in [  # type: ignore
            "GGG2014", "GGG2020"
        ]:
            if alg == "proffast-1.0" and atm == "GGG2020":
                continue
            for sdc in SENSOR_DATA_CONTEXTS:
                # set up container factory
                src.retrieval.utils.retrieval_status.RetrievalStatusList.add_items(
                    [sdc],
                    alg,
                    atm,
                )
                # create session and run container
                session = src.retrieval.session.create_session.run(
                    container_factory,
                    sdc,
                    retrieval_algorithm=alg,
                    atmospheric_profile_model=atm,
                    job_settings=src.types.config.RetrievalJobSettingsConfig(
                        # test this for all alg/atm combinations
                        # for one of the sensor data contexts
                        use_local_pressure_in_pcxs=(
                            sdc.from_datetime.date() == datetime.date(
                                2017, 6, 9
                            )
                        ),
                    )
                )
                name = (
                    f"{session.ctn.container_id}:{alg}-{atm}-" +
                    f"{sdc.sensor_id}-{sdc.from_datetime.date()}"
                )
                p = multiprocessing.Process(
                    target=run_session,
                    args=(session, config, only_run_mock_retrieval),
                    name=name,
                    daemon=True,
                )
                pending_processes.append(p)

    active_processes: list[multiprocessing.Process] = []
    finished_processes: list[multiprocessing.Process] = []

    cpu_count = multiprocessing.cpu_count()
    print(f"Detected {cpu_count} CPU cores")
    process_count = max(1, cpu_count - 1)
    print(f"Running {process_count} processes in parallel")

    # wait for all processes to finish
    while True:
        while ((len(active_processes) < process_count) and
               (len(pending_processes) > 0)):
            p = pending_processes.pop(0)
            print(f"Starting process {p.name}")
            p.start()
            active_processes.append(p)
            print(f"Started process {p.name}")

        time.sleep(0.5)

        newly_finished_processes: list[multiprocessing.Process] = []
        for p in active_processes:
            if not p.is_alive():
                newly_finished_processes.append(p)

        for p in newly_finished_processes:
            print(f"Joining process {p.name}")
            p.join()
            active_processes.remove(p)
            container_factory.remove_container(p.name.split(":")[0])
            finished_processes.append(p)
            print(f"Finished process {p.name}")

        if len(active_processes) == 0 and len(pending_processes) == 0:
            break

        time.sleep(1)
        print("Waiting ...")
        print(
            f"Pending | Active | Finished: {len(pending_processes)} |" +
            f" {len(active_processes)} | {len(finished_processes)}"
        )


def _point_config_to_test_data(config: src.types.Config) -> None:
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


def _assert_output_correctness(
    retrieval_algorithm: src.types.RetrievalAlgorithm,
    atmospheric_profile_model: src.types.AtmosphericProfileModel,
    sensor_data_context: em27_metadata.types.SensorDataContext,
) -> None:
    date_string = sensor_data_context.from_datetime.strftime("%Y%m%d")
    out_path = os.path.join(
        PROJECT_DIR, "data/testing/container/outputs", retrieval_algorithm,
        atmospheric_profile_model, sensor_data_context.sensor_id, "successful",
        date_string
    )
    expected_files = [
        "about.json",
        "logfiles/container.log",
    ]
    if retrieval_algorithm in ["proffast-2.2", "proffast-2.3"]:
        expected_files.extend([
            (
                f"comb_invparms_{sensor_data_context.sensor_id}_" +
                f"SN{str(sensor_data_context.serial_number).zfill(3)}" +
                f"_{date_string[2:]}-{date_string[2:]}.csv"
            ),
            "pylot_config.yml",
            "pylot_log_format.yml",
            "logfiles/preprocess_output.log",
            "logfiles/pcxs_output.log",
            "logfiles/inv_output.log",
        ])
    if retrieval_algorithm == "proffast-1.0":
        expected_files.extend([
            (
                f"{sensor_data_context.sensor_id}{date_string[2:]}-" +
                f"combined-invparms.csv"
            ),
            (
                f"{sensor_data_context.sensor_id}{date_string[2:]}-" +
                f"combined-invparms.parquet"
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
