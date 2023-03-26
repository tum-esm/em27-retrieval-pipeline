import json
import os
import pytest
import tum_esm_em27_metadata
from src import custom_types, interfaces, utils
from ..fixtures import provide_tmp_config
import dotenv

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
dotenv.load_dotenv(os.path.join(PROJECT_DIR, "tests", ".env"))


@pytest.mark.ci
def test_retrieval_queue(provide_tmp_config: custom_types.Config) -> None:
    config = provide_tmp_config
    config.automated_proffast.process_data_automatically = True
    config.automated_proffast.data_filter.sensor_ids_to_consider = ["so"]
    config.automated_proffast.data_filter.from_date = "20170608"
    config.automated_proffast.data_filter.to_date = "20170609"

    logger = utils.automated_proffast.Logger("testing", print_only=True)

    locations = [
        tum_esm_em27_metadata.types.Location(
            location_id="LOC1",
            details="...",
            lat=0.0,
            lon=0.0,
            alt=0.0,
        )
    ]
    sensors = [
        tum_esm_em27_metadata.types.Sensor(
            sensor_id="so",
            serial_number=1,
            utc_offsets=[
                tum_esm_em27_metadata.types.SensorUTCOffset(
                    from_date="20170608", to_date="20170609", utc_offset=0
                )
            ],
            different_pressure_data_source=[],
            pressure_calibration_factors=[
                tum_esm_em27_metadata.types.SensorPressureCalibrationFactor(
                    from_date="20170608", to_date="20170609", factor=1.0
                ),
            ],
            locations=[
                tum_esm_em27_metadata.types.SensorLocation(
                    from_date="20170608", to_date="20170609", location_id="LOC1"
                )
            ],
        )
    ]

    retrieval_queue = interfaces.automated_proffast.RetrievalQueue(
        config,
        logger,
        em27_metadata=tum_esm_em27_metadata.interfaces.EM27MetadataInterface(
            locations=locations, sensors=sensors, campaigns=[]
        ),
    )

    next_item_1 = retrieval_queue.get_next_item()
    print(f"next_item_1: {next_item_1}")
    assert next_item_1.sensor_id == "so"
    assert next_item_1.date == "20170609"

    next_item_2 = retrieval_queue.get_next_item()
    print(f"next_item_2: {next_item_2}")
    assert next_item_2.sensor_id == "so"
    assert next_item_2.date == "20170608"

    next_item_3 = retrieval_queue.get_next_item()
    print(f"next_item_3: {next_item_3}")
    assert next_item_3 is None
