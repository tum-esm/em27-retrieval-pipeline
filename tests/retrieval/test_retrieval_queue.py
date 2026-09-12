import datetime
import os
import pytest
import dotenv
import tum_esm_utils
from ..fixtures import (
    provide_config_template,  # pyright: ignore[reportUnusedImport]
    remove_temporary_retrieval_data,  # pyright: ignore[reportUnusedImport]
)

from src import types, retrieval, em27_metadata
from src.retrieval.dispatching.retrieval_queue import generate_retrieval_queue

dir = os.path.dirname
PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "tests", ".env"))

em27_metadata_interface = em27_metadata.interfaces.EM27MetadataInterface(
    locations=em27_metadata.types.LocationMetadataList(
        root=[
            em27_metadata.types.LocationMetadata(
                location_id="SOD",
                details="Sodankyla",
                lon=26.630,
                lat=67.366,
                alt_asl=181.0,
            )
        ]
    ),
    sensors=em27_metadata.types.SensorMetadataList(
        root=[
            em27_metadata.types.SensorMetadata(
                sensor_id="so",
                serial_number=1,
                deployments=[
                    em27_metadata.types.Deployment(
                        from_datetime="2017-01-01T00:00:00+0000",  # pyright: ignore[reportArgumentType]
                        to_datetime="2017-12-31T23:59:59+0000",  # pyright: ignore[reportArgumentType]
                        location_id="SOD",
                    )
                ],
            )
        ]
    ),
    campaigns=em27_metadata.types.CampaignMetadataList(root=[]),
)


def _check_retrieval_queue(
    expected: list[datetime.date],
    actual: list[em27_metadata.types.SensorDataContext],
) -> None:
    assert len(expected) == len(actual)
    for expected_item, actual_item in zip(expected, actual):
        assert actual_item.from_datetime.date() == expected_item
        assert actual_item.to_datetime.date() == expected_item


@pytest.mark.order(3)
@pytest.mark.quick
def test_retrieval_queue(
    remove_temporary_retrieval_data: None,
    provide_config_template: types.Config,
) -> None:
    config = provide_config_template
    logger = retrieval.utils.logger.Logger("pytest", write_to_file=False, print_to_console=True)
    assert config.retrieval is not None
    config.retrieval.general.queue_verbosity = "verbose"

    # target config at test data
    config.data.ground_pressure.path.root = os.path.join(
        PROJECT_DIR, "example", "data", "inputs", "ground-pressure"
    )
    config.data.ground_pressure.pressure_column = "BaroYoung"
    config.data.ground_pressure.pressure_column_format = "hPa"
    config.data.ground_pressure.file_regex = (
        "^ground-pressure-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).csv$"
    )
    config.data.ground_pressure.date_column = "utc-date"
    config.data.ground_pressure.date_column_format = "%Y-%m-%d"
    config.data.ground_pressure.time_column = "utc-time"
    config.data.ground_pressure.time_column_format = "%H:%M:%S"

    config.data.interferograms.path.root = os.path.join(
        PROJECT_DIR, "example", "data", "inputs", "interferograms"
    )
    config.data.atmospheric_profiles.path.root = os.path.join(
        PROJECT_DIR, "example", "data", "inputs", "atmospheric-profiles"
    )
    config.data.results.path.root = os.path.join(
        PROJECT_DIR, "data", "testing", "outputs", "individual-results"
    )

    # test case 1
    retrieval_queue = generate_retrieval_queue(
        config,
        logger,
        em27_metadata_interface=em27_metadata_interface,
        retrieval_job_config=types.RetrievalSubConfigs.Job(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date="2017-06-09",
            to_date="2017-06-10",
        ),
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
        logger,
        em27_metadata_interface=em27_metadata_interface,
        retrieval_job_config=types.RetrievalSubConfigs.Job(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date="2017-06-01",
            to_date="2017-06-10",
        ),
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
        logger,
        em27_metadata_interface=em27_metadata_interface,
        retrieval_job_config=types.RetrievalSubConfigs.Job(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date="2017-06-01",
            to_date="2017-06-08",
        ),
    )
    _check_retrieval_queue(
        expected=[datetime.date(2017, 6, 8)],
        actual=retrieval_queue,
    )

    # test case 4
    retrieval_queue = generate_retrieval_queue(
        config,
        logger,
        em27_metadata_interface=em27_metadata_interface,
        retrieval_job_config=types.RetrievalSubConfigs.Job(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date="2017-06-08",
            to_date="2017-06-08",
        ),
    )
    _check_retrieval_queue(
        expected=[datetime.date(2017, 6, 8)],
        actual=retrieval_queue,
    )

    # test case 5
    retrieval_queue = generate_retrieval_queue(
        config,
        logger,
        em27_metadata_interface=em27_metadata_interface,
        retrieval_job_config=types.RetrievalSubConfigs.Job(
            retrieval_algorithm="proffast-2.2",
            atmospheric_profile_model="GGG2014",
            sensor_ids=["so"],
            from_date="2017-06-01",
            to_date="2017-06-07",
        ),
    )
    _check_retrieval_queue(
        expected=[],
        actual=retrieval_queue,
    )
