from typing import Any, Generator
import datetime
import os
import time
import pytest
import em27_metadata
import tum_esm_utils
import multiprocessing
import src
import polars as pl
from tests.fixtures import (
    wrap_test_with_mainlock,
    download_sample_data,
    provide_config_template,
    remove_temporary_retrieval_data,
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
    )
    for date in [
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
    )
    for date in [
        datetime.date(2022, 6, 2),
    ]
]


@pytest.fixture(scope="session")
def provide_container_factory_for_ci_tests(
    provide_config_template: src.types.Config,
) -> Generator[src.retrieval.dispatching.container_factory.ContainerFactory, None, None]:
    logger = src.retrieval.utils.logger.Logger(
        "pytest",
        write_to_file=False,
        print_to_console=True,
    )
    yield src.retrieval.dispatching.container_factory.ContainerFactory(
        provide_config_template, logger, mode="ci-tests"
    )


@pytest.fixture(scope="session")
def provide_container_factory_for_complete_tests(
    provide_config_template: src.types.Config,
) -> Generator[src.retrieval.dispatching.container_factory.ContainerFactory, None, None]:
    logger = src.retrieval.utils.logger.Logger(
        "pytest",
        write_to_file=False,
        print_to_console=True,
    )
    yield src.retrieval.dispatching.container_factory.ContainerFactory(
        provide_config_template, logger, mode="complete-tests"
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
    provide_container_factory_for_ci_tests: src.retrieval.dispatching.container_factory.ContainerFactory,
) -> None:
    config = provide_config_template
    container_factory = provide_container_factory_for_ci_tests

    _point_config_to_test_data(config)
    assert config.retrieval is not None

    pending_jobs = _generate_job_list()
    print("Running in serial mode")
    for i, j in enumerate(pending_jobs):
        print(f"#{i}: Spinning up new session")
        session = src.retrieval.session.create_session.run(
            container_factory,
            j[2],
            retrieval_algorithm=j[0],
            atmospheric_profile_model=j[1],
            job_settings=src.types.config.RetrievalJobSettingsConfig(
                # test this for all alg/atm combinations
                # for one of the sensor data contexts
                use_local_pressure_in_pcxs=(j[2].from_datetime.date() == datetime.date(2017, 6, 9)),
                store_binary_spectra=True,
            ),
        )
        print(f"#{i}: Running session")
        run_session(session, config, True)
        print(f"#{i}: Finished session")
        container_factory.remove_container(session.ctn.container_id)


# this test will run the actual retrieval algorithm
@pytest.mark.order(5)
@pytest.mark.complete
def test_container_lifecycle_complete(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    remove_temporary_retrieval_data: None,
    provide_config_template: src.types.Config,
    provide_container_factory_for_complete_tests: src.retrieval.dispatching.container_factory.ContainerFactory,
) -> None:
    config = provide_config_template
    container_factory = provide_container_factory_for_complete_tests

    _point_config_to_test_data(config)
    assert config.retrieval is not None

    pending_jobs = _generate_job_list()
    active_processes: list[Any] = []
    finished_processes: list[Any] = []

    cpu_count = multiprocessing.cpu_count()
    print(f"Detected {cpu_count} CPU cores")
    process_count = max(1, cpu_count - 1)
    print(f"Running {process_count} processes in parallel")

    # wait for all processes to finish
    while True:
        while (len(active_processes) < process_count) and (len(pending_jobs) > 0):
            j = pending_jobs.pop(0)
            print(f"Spinning up new session")
            session = src.retrieval.session.create_session.run(
                container_factory,
                j[2],
                retrieval_algorithm=j[0],
                atmospheric_profile_model=j[1],
                job_settings=src.types.config.RetrievalJobSettingsConfig(
                    # test this for all alg/atm combinations
                    # for one of the sensor data contexts
                    use_local_pressure_in_pcxs=(
                        j[2].from_datetime.date() == datetime.date(2017, 6, 9)
                    ),
                    store_binary_spectra=True,
                ),
            )
            print(f"Creating new process")
            p = multiprocessing.get_context("spawn").Process(
                target=run_session,
                args=(session, config, False),
                name=(
                    f"{session.ctn.container_id}:{j[0]}-{j[1]}-"
                    + f"{j[2].sensor_id}-{j[2].from_datetime.date()}"
                ),
            )
            print(f"Starting process {p.name}")
            p.start()
            active_processes.append(p)
            print(f"Started process {p.name}")

        time.sleep(0.5)

        newly_finished_processes: list[Any] = []
        for p in active_processes:
            if not p.is_alive():
                newly_finished_processes.append(p)

        for p in newly_finished_processes:
            print(f"Joining process {p.name}")
            p.join()
            assert p.exitcode == 0, f"Process {p.name} failed"
            active_processes.remove(p)
            container_factory.remove_container(p.name.split(":")[0])
            finished_processes.append(p)
            p.close()
            print(f"Finished process {p.name}")

        if len(active_processes) == 0 and len(pending_jobs) == 0:
            break

        time.sleep(2)
        print(
            f"Pending | Active | Finished: {len(pending_jobs)} |"
            + f" {len(active_processes)} | {len(finished_processes)}"
        )


def run_session(
    session: src.types.RetrievalSession, config: src.types.Config, only_run_mock_retrieval: bool
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


def _generate_job_list() -> list[
    tuple[
        src.types.RetrievalAlgorithm,
        src.types.AtmosphericProfileModel,
        em27_metadata.types.SensorDataContext,
    ]
]:
    src.retrieval.utils.retrieval_status.RetrievalStatusList.reset()

    pending_jobs: list[
        tuple[
            src.types.RetrievalAlgorithm,
            src.types.AtmosphericProfileModel,
            em27_metadata.types.SensorDataContext,
        ]
    ] = []

    # start proffast 1.0 first because it takes the longest
    for alg in ["proffast-1.0", "proffast-2.2", "proffast-2.3", "proffast-2.4", "proffast-2.4.1"]:
        for atm in ["GGG2014", "GGG2020"]:
            if alg == "proffast-1.0" and atm == "GGG2020":
                continue
            for sdc in SENSOR_DATA_CONTEXTS:
                src.retrieval.utils.retrieval_status.RetrievalStatusList.add_items(
                    [sdc],
                    alg,  # type: ignore
                    atm,  # type: ignore
                )
                pending_jobs.append((alg, atm, sdc))  # type: ignore

    print(f"Jobs ({len(pending_jobs)}):")
    for i, j in enumerate(pending_jobs):
        print(f"  #{i}: {j[0]} | {j[1]} | {j[2].sensor_id} | {j[2].from_datetime.date()}")

    return pending_jobs


def _point_config_to_test_data(config: src.types.Config) -> None:
    config.general.data.ground_pressure.path.root = os.path.join(
        PROJECT_DIR, "data", "testing", "inputs", "data", "log"
    )
    config.general.data.ground_pressure.file_regex = (
        "^ground-pressure-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).csv$"
    )
    config.general.data.ground_pressure.date_column = "utc-date"
    config.general.data.ground_pressure.date_column_format = "%Y-%m-%d"
    config.general.data.ground_pressure.time_column = "utc-time"
    config.general.data.ground_pressure.time_column_format = "%H:%M:%S"
    config.general.data.ground_pressure.pressure_column = "pressure"
    config.general.data.ground_pressure.pressure_column_format = "hPa"

    config.general.data.interferograms.root = os.path.join(
        PROJECT_DIR, "data", "testing", "inputs", "data", "ifg"
    )
    config.general.data.atmospheric_profiles.root = os.path.join(
        PROJECT_DIR, "data", "testing", "inputs", "data", "map"
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
        PROJECT_DIR,
        "data/testing/container/outputs",
        retrieval_algorithm,
        atmospheric_profile_model,
        sensor_data_context.sensor_id,
        "successful",
        date_string,
    )
    expected_files = [
        "about.json",
        "logfiles/container.log",
    ]
    output_csv_name: str
    if retrieval_algorithm == "proffast-1.0":
        output_csv_name = f"{sensor_data_context.sensor_id}{date_string[2:]}-combined-invparms.csv"
        expected_files.extend(
            [
                output_csv_name,
                (f"{sensor_data_context.sensor_id}{date_string[2:]}-combined-invparms.parquet"),
                "logfiles/wrapper.log",
                "logfiles/preprocess4.log",
                "logfiles/pcxs10.log",
                "logfiles/invers10.log",
            ]
        )
    elif retrieval_algorithm in ["proffast-2.2", "proffast-2.3", "proffast-2.4", "proffast-2.4.1"]:
        output_csv_name = (
            f"comb_invparms_{sensor_data_context.sensor_id}_"
            + f"SN{str(sensor_data_context.serial_number).zfill(3)}"
            + f"_{date_string[2:]}-{date_string[2:]}.csv"
        )
        expected_files.extend(
            [
                output_csv_name,
                (
                    "pylot_config.yml"
                    if (retrieval_algorithm in ["proffast-2.2", "proffast-2.3", "proffast-2.4"])
                    else "proffastpylot_parameters.yml"
                ),
                "pylot_log_format.yml",
                "logfiles/preprocess_output.log",
                "logfiles/pcxs_output.log",
                "logfiles/inv_output.log",
            ]
        )
    else:
        raise Exception("This should not happen")

    for filename in expected_files:
        filepath = os.path.join(out_path, filename)
        assert os.path.isfile(filepath), f"output file does not exist ({filepath})"

    pT_dir_path = os.path.join(out_path, "analysis", "pT")
    assert os.path.isdir(pT_dir_path), f"pT path does not exist: {pT_dir_path}"

    cal_dir_path = os.path.join(out_path, "analysis", "cal")
    assert os.path.isdir(cal_dir_path), f"cal path does not exist: {cal_dir_path}"

    df = pl.read_csv(os.path.join(out_path, output_csv_name))
    df = df.rename({col: col.strip() for col in df.columns})
    good_data_only = df.filter(
        pl.col("XAIR")
        .cast(pl.Utf8)
        .str.strip_chars(" ")
        .cast(pl.Float64)
        .is_between(0.99 * 0.9983, 1.01 * 0.9983)
    )
    assert len(good_data_only) == len(df), "XAIR values indicate an input data issue"
