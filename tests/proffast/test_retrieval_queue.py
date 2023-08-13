import datetime
import os
from typing import Optional
import pytest
import tum_esm_em27_metadata
from src import custom_types, interfaces, utils
from ..fixtures import provide_proffast_config
import dotenv

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "tests", ".env"))

em27_metadata = tum_esm_em27_metadata.interfaces.EM27MetadataInterface(
    locations=[
        tum_esm_em27_metadata.types.LocationMetadata(
            location_id="LOC1",
            details="...",
            lat=0.0,
            lon=0.0,
            alt=0.0,
        )
    ],
    sensors=[
        tum_esm_em27_metadata.types.SensorMetadata(
            sensor_id="so",
            serial_number=1,
            different_utc_offsets=[],
            different_pressure_data_sources=[],
            different_pressure_calibration_factors=[],
            different_output_calibration_factors=[],
            locations=[
                tum_esm_em27_metadata.types.SensorTypes.Location(
                    from_datetime="2017-01-01T00:00:00+00:00",
                    to_datetime="2017-12-31T23:59:59+00:00",
                    location_id="LOC1",
                )
            ],
        )
    ],
    campaigns=[],
)


def check_next_item(
    i: Optional[tum_esm_em27_metadata.types.SensorDataContext],
    expected_date: Optional[datetime.date],
) -> None:
    if i is None:
        assert expected_date is None
    else:
        assert i.from_datetime == expected_date


@pytest.mark.ci
def test_retrieval_queue(
    provide_proffast_config: custom_types.Config,
) -> None:
    config = provide_proffast_config
    assert config.automated_proffast is not None

    config.automated_proffast.data_filter.from_date = datetime.date(2017, 6, 8)
    config.automated_proffast.data_filter.to_date = datetime.date(2017, 6, 9)
    logger = utils.proffast.Logger("testing", print_only=True)

    # test case 1
    config.automated_proffast.data_filter.from_date = datetime.date(2017, 6, 9)
    config.automated_proffast.data_filter.to_date = datetime.date(2017, 6, 10)
    retrieval_queue = interfaces.proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata, verbose_reasoning=True
    )
    check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 9))
    check_next_item(retrieval_queue.get_next_item(), None)
    check_next_item(retrieval_queue.get_next_item(), None)

    # test case 2
    config.automated_proffast.data_filter.from_date = datetime.date(2017, 6, 1)
    config.automated_proffast.data_filter.to_date = datetime.date(2017, 6, 10)
    retrieval_queue = interfaces.proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata
    )
    check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 9))
    check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 8))
    check_next_item(retrieval_queue.get_next_item(), None)
    check_next_item(retrieval_queue.get_next_item(), None)

    # test case 3
    config.automated_proffast.data_filter.from_date = datetime.date(2017, 6, 1)
    config.automated_proffast.data_filter.to_date = datetime.date(2017, 6, 8)
    retrieval_queue = interfaces.proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata
    )
    check_next_item(retrieval_queue.get_next_item(), datetime.date(2017, 6, 8))
    check_next_item(retrieval_queue.get_next_item(), None)
    check_next_item(retrieval_queue.get_next_item(), None)

    # test case 4
    config.automated_proffast.data_filter.from_date = datetime.date(2017, 6, 1)
    config.automated_proffast.data_filter.to_date = datetime.date(2017, 6, 7)
    retrieval_queue = interfaces.proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata
    )
    check_next_item(retrieval_queue.get_next_item(), None)
    check_next_item(retrieval_queue.get_next_item(), None)
