import datetime
import os
import pytest
import em27_metadata
import tum_esm_utils
from ..fixtures import download_sample_data, clear_output_data, provide_config_template
import dotenv

from src import types
from src.retrieval.dispatching.retrieval_queue import generate_retrieval_queue

dir = os.path.dirname
PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "tests", ".env"))

em27_metadata_storage = em27_metadata.interfaces.EM27MetadataInterface(
    locations=[
        em27_metadata.types.LocationMetadata(
            location_id="SOD",
            details="Sodankyla",
            lon=26.630,
            lat=67.366,
            alt=181.0,
        )
    ],
    sensors=[
        em27_metadata.types.SensorMetadata(
            sensor_id="so",
            serial_number=1,
            different_utc_offsets=[],
            different_pressure_data_sources=[],
            different_pressure_calibration_factors=[],
            different_output_calibration_factors=[],
            locations=[
                em27_metadata.types.SensorTypes.Location(
                    from_datetime="2017-01-01T00:00:00+00:00",
                    to_datetime="2017-12-31T23:59:59+00:00",
                    location_id="SOD",
                )
            ],
        )
    ],
    campaigns=[],
)


def _check_retrieval_queue(
    expected: list[datetime.date],
    actual: list[em27_metadata.types.SensorDataContext],
) -> None:
    assert len(expected) == len(actual)
    for expected_item, actual_item in zip(expected, actual):
        assert actual_item.from_datetime.date() == expected_item
        assert actual_item.to_datetime.date() == expected_item


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_retrieval_queue(
    download_sample_data: None,
    clear_output_data: None,
    provide_config_template: types.Config,
) -> None:
    config = provide_config_template
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

    # test case 1
    retrieval_queue = generate_retrieval_queue(
        config,
        em27_metadata_interface=em27_metadata_storage,
        retrieval_job_config=types.RetrievalJobConfig(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date=datetime.date(2017, 6, 9),
            to_date=datetime.date(2017, 6, 10),
        )
    )
    _check_retrieval_queue(
        expected=[
            datetime.date(2017, 6, 9),
        ],
        actual=retrieval_queue,
    )

    # test case 2
    retrieval_queue = generate_retrieval_queue(
        config,
        em27_metadata_interface=em27_metadata_storage,
        retrieval_job_config=types.RetrievalJobConfig(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date=datetime.date(2017, 6, 1),
            to_date=datetime.date(2017, 6, 10),
        )
    )
    _check_retrieval_queue(
        expected=[
            datetime.date(2017, 6, 9),
            datetime.date(2017, 6, 8),
        ],
        actual=retrieval_queue,
    )

    # test case 3
    retrieval_queue = generate_retrieval_queue(
        config,
        em27_metadata_interface=em27_metadata_storage,
        retrieval_job_config=types.RetrievalJobConfig(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date=datetime.date(2017, 6, 1),
            to_date=datetime.date(2017, 6, 8),
        )
    )
    _check_retrieval_queue(
        expected=[datetime.date(2017, 6, 8)],
        actual=retrieval_queue,
    )

    # test case 4
    retrieval_queue = generate_retrieval_queue(
        config,
        em27_metadata_interface=em27_metadata_storage,
        retrieval_job_config=types.RetrievalJobConfig(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date=datetime.date(2017, 6, 8),
            to_date=datetime.date(2017, 6, 8),
        )
    )
    _check_retrieval_queue(
        expected=[datetime.date(2017, 6, 8)],
        actual=retrieval_queue,
    )

    # test case 5
    retrieval_queue = generate_retrieval_queue(
        config,
        em27_metadata_interface=em27_metadata_storage,
        retrieval_job_config=types.RetrievalJobConfig(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date=datetime.date(2017, 6, 1),
            to_date=datetime.date(2017, 6, 7),
        )
    )
    _check_retrieval_queue(
        expected=[],
        actual=retrieval_queue,
    )
