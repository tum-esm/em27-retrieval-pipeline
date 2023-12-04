import datetime
import os
from typing import Optional
import pytest
import em27_metadata
import tum_esm_utils

from src.utils import utils
from ..fixtures import download_sample_data, clear_output_data, provide_config_template
import dotenv

from src import retrieval

dir = os.path.dirname
PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "tests", ".env"))

em27_metadata_storage = em27_metadata.interfaces.EM27MetadataInterface(
    locations=[
        em27_metadata.types.LocationMetadata(
            location_id="LOC1",
            details="...",
            lat=0.0,
            lon=0.0,
            alt=0.0,
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
                    location_id="LOC1",
                )
            ],
        )
    ],
    campaigns=[],
)


def _check_next_item(
    i: Optional[em27_metadata.types.SensorDataContext],
    expected_date: Optional[datetime.date],
) -> None:
    if i is None:
        assert expected_date is None
    else:
        assert i.from_datetime.date() == expected_date


@pytest.mark.order(1)
@pytest.mark.ci_quick
@pytest.mark.ci_intensive
@pytest.mark.ci_complete
def test_retrieval_queue(
    download_sample_data: None,
    clear_output_data: None,
    provide_config_template: utils.config.Config,
) -> None:
    config = provide_config_template
    assert config.retrieval is not None

    # target config at test data
    config.retrieval.data_filter.sensor_ids_to_consider = ["so"]
    config.retrieval.general.retrieval_software = "proffast-2.2"
    config.general.data_src_dirs.datalogger = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "log"
    )
    config.general.data_src_dirs.interferograms = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "ifg"
    )
    config.general.data_src_dirs.profiles = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "inputs", "map"
    )
    config.general.data_dst_dirs.results = os.path.join(
        PROJECT_DIR, "data", "testing", "container", "outputs"
    )

    config.retrieval.data_filter.from_date = datetime.date(2017, 6, 8)
    config.retrieval.data_filter.to_date = datetime.date(2017, 6, 9)
    logger = retrieval.utils.logger.Logger("testing", print_only=True)

    # test case 1
    config.retrieval.data_filter.from_date = datetime.date(2017, 6, 9)
    config.retrieval.data_filter.to_date = datetime.date(2017, 6, 10)
    retrieval_queue = retrieval.dispatching.retrieval_queue.RetrievalQueue(
        config,
        logger,
        em27_metadata_storage=em27_metadata_storage,
        verbose_reasoning=True
    )
    _check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 9))
    _check_next_item(retrieval_queue.get_next_item(), None)
    _check_next_item(retrieval_queue.get_next_item(), None)

    # test case 2
    config.retrieval.data_filter.from_date = datetime.date(2017, 6, 1)
    config.retrieval.data_filter.to_date = datetime.date(2017, 6, 10)
    retrieval_queue = retrieval.dispatching.retrieval_queue.RetrievalQueue(
        config, logger, em27_metadata_storage=em27_metadata_storage
    )
    _check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 9))
    _check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 8))
    _check_next_item(retrieval_queue.get_next_item(), None)
    _check_next_item(retrieval_queue.get_next_item(), None)

    # test case 3
    config.retrieval.data_filter.from_date = datetime.date(2017, 6, 1)
    config.retrieval.data_filter.to_date = datetime.date(2017, 6, 8)
    retrieval_queue = retrieval.dispatching.retrieval_queue.RetrievalQueue(
        config, logger, em27_metadata_storage=em27_metadata_storage
    )
    _check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 8))
    _check_next_item(retrieval_queue.get_next_item(), None)
    _check_next_item(retrieval_queue.get_next_item(), None)

    # test case 4
    config.retrieval.data_filter.from_date = datetime.date(2017, 6, 8)
    config.retrieval.data_filter.to_date = datetime.date(2017, 6, 8)
    retrieval_queue = retrieval.dispatching.retrieval_queue.RetrievalQueue(
        config, logger, em27_metadata_storage=em27_metadata_storage
    )
    _check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 8))
    _check_next_item(retrieval_queue.get_next_item(), None)
    _check_next_item(retrieval_queue.get_next_item(), None)

    # test case 5
    config.retrieval.data_filter.from_date = datetime.date(2017, 6, 1)
    config.retrieval.data_filter.to_date = datetime.date(2017, 6, 7)
    retrieval_queue = retrieval.dispatching.retrieval_queue.RetrievalQueue(
        config, logger, em27_metadata_storage=em27_metadata_storage
    )
    _check_next_item(retrieval_queue.get_next_item(), None)
    _check_next_item(retrieval_queue.get_next_item(), None)
