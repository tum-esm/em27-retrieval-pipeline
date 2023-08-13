import datetime
import pytest

import tum_esm_em27_metadata
from tests.fixtures import (
    wrap_test_with_mainlock,
    download_sample_data,
    provide_proffast_config,
    clear_output_data,
)
from src import custom_types, utils, interfaces, procedures

SENSOR_DATA_CONTEXTS = [
    tum_esm_em27_metadata.types.SensorDataContext(
        sensor_id="so",
        serial_number=39,
        from_datetime=datetime.datetime.fromisoformat(date + "T00:00:00+00:00"),
        to_datetime=datetime.datetime.fromisoformat(date + "T23:59:59+00:00"),
        utc_offset=0,
        pressure_data_source="so",
        pressure_calibration_factor=1,
        output_calibration_factors_xco2=[],
        output_calibration_factors_xch4=[],
        output_calibration_factors_xco=[],
        output_calibration_scheme=None,
        multiple_ctx_on_this_date=False,
        location=tum_esm_em27_metadata.types.LocationMetadata(
            location_id="SOD",
            details="Sodankyla",
            lon=26.630,
            lat=67.366,
            alt=181.0,
        ),
    )
    for date in ["2017-06-08", "2017-06-09"]
] + [
    tum_esm_em27_metadata.types.SensorDataContext(
        sensor_id="mc",
        serial_number=115,
        from_datetime=datetime.datetime.fromisoformat(date + "T00:00:00+00:00"),
        to_datetime=datetime.datetime.fromisoformat(date + "T23:59:59+00:00"),
        utc_offset=0,
        pressure_data_source="mc",
        pressure_calibration_factor=1,
        output_calibration_factors_xco2=[],
        output_calibration_factors_xch4=[],
        output_calibration_factors_xco=[],
        output_calibration_scheme=None,
        multiple_ctx_on_this_date=False,
        location=tum_esm_em27_metadata.types.LocationMetadata(
            location_id="ZEN",
            details="Zentralfriedhof",
            lon=16.438481,
            lat=48.147699,
            alt=180.0,
        ),
    )
    for date in ["2022-06-02"]
]


@pytest.mark.integration
def test_container(
    wrap_test_with_mainlock: None,
    download_sample_data: None,
    clear_output_data: None,
    provide_proffast_config: custom_types.Config,
) -> None:
    # set up container
    logger = utils.proffast.Logger("pytest", print_only=True)
    pylot_factory = interfaces.proffast.PylotFactory(logger)

    for sdc in SENSOR_DATA_CONTEXTS:
        # create session
        session = procedures.proffast.create_session.run(pylot_factory, sdc)

        # run container
        procedures.proffast.process_session.run(provide_proffast_config, session)

        # assert output correctness
        # TODO
