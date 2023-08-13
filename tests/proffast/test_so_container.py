import pytest
import os

import tum_esm_em27_metadata
from tests.fixtures import (
    wrap_test_with_mainlock,
    download_sample_data,
    provide_container_config,
    clear_output_data,
)
from src import custom_types, utils, interfaces, procedures

# TODO: test mc container in here

SENSOR_DATA_CONTEXTS = [
    tum_esm_em27_metadata.types.SensorDataContext(
        sensor_id="so",
        serial_number=39,
        utc_offset=0.0,
        pressure_data_source="so",
        pressure_calibration_factor=1,
        output_calibration_factor=1,
        date=date,
        location=tum_esm_em27_metadata.types.LocationMetadata(
            location_id="SOD",
            details="Sodankyla",
            lon=26.630,
            lat=67.366,
            alt=181.0,
        ),
    )
    for date in ["20170608", "20170609"]
]


@pytest.mark.integration
def test_so_container(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    clear_output_data: None,
    provide_container_config: custom_types.Config,
) -> None:
    # set up container
    logger = utils.proffast.Logger("pytest", print_only=True)
    pylot_factory = interfaces.proffast.PylotFactory(logger)
    session = procedures.proffast.create_session.run(
        pylot_factory, SENSOR_DATA_CONTEXTS[0]
    )

    # run container
    procedures.proffast.process_session.run(provide_container_config, session)

    # assert output correctness
    # TODO
