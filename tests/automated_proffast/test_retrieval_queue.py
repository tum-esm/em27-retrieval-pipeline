import json
import os
from typing import Optional
import pytest
import tum_esm_em27_metadata
from src import custom_types, interfaces, utils
from ..fixtures import provide_tmp_config, provide_tmp_manual_queue
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
                    from_date="20170101", to_date="20171231", location_id="LOC1"
                )
            ],
        )
    ],
    campaigns=[],
)


def check_next_item(
    i: Optional[tum_esm_em27_metadata.types.SensorDataContext],
    expected_date: Optional[str],
) -> None:
    if i is None:
        assert expected_date is None
    else:
        assert i.date == expected_date


@pytest.mark.ci
def test_retrieval_queue(
    provide_tmp_config: custom_types.Config,
    provide_tmp_manual_queue: custom_types.ManualQueue,
) -> None:
    config = provide_tmp_config
    config.automated_proffast.storage_data_filter.from_date = "20170608"
    config.automated_proffast.storage_data_filter.to_date = "20170609"
    logger = utils.automated_proffast.Logger("testing", print_only=True)

    # test queue when no data is available
    config.automated_proffast.data_sources.storage = False
    config.automated_proffast.data_sources.manual_queue = False
    retrieval_queue = interfaces.automated_proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata
    )
    check_next_item(retrieval_queue.get_next_item(), None)

    # test queue when only stored data is available
    config.automated_proffast.data_sources.storage = True
    config.automated_proffast.data_sources.manual_queue = False
    retrieval_queue = interfaces.automated_proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata
    )
    check_next_item(retrieval_queue.get_next_item(), "20170609")
    check_next_item(retrieval_queue.get_next_item(), "20170608")
    check_next_item(retrieval_queue.get_next_item(), None)

    # test queue when only manual queue data is available
    config.automated_proffast.data_sources.storage = False
    config.automated_proffast.data_sources.manual_queue = True
    retrieval_queue = interfaces.automated_proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata
    )
    check_next_item(retrieval_queue.get_next_item(), "20170103")
    check_next_item(retrieval_queue.get_next_item(), "20170101")
    check_next_item(retrieval_queue.get_next_item(), "20170102")
    check_next_item(retrieval_queue.get_next_item(), None)

    # test queue when there is both manual queue data and stored data
    config.automated_proffast.data_sources.storage = True
    config.automated_proffast.data_sources.manual_queue = True
    retrieval_queue = interfaces.automated_proffast.RetrievalQueue(
        config, logger, em27_metadata=em27_metadata
    )
    check_next_item(retrieval_queue.get_next_item(), "20170103")
    check_next_item(retrieval_queue.get_next_item(), "20170101")
    check_next_item(retrieval_queue.get_next_item(), "20170609")
    check_next_item(retrieval_queue.get_next_item(), "20170608")
    check_next_item(retrieval_queue.get_next_item(), "20170102")
    check_next_item(retrieval_queue.get_next_item(), None)
