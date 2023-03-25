import pytest
import shutil
import os

import tum_esm_em27_metadata
from tests.fixtures import wrap_test_with_mainlock, download_sample_data, PROJECT_DIR
from src import custom_types, utils, interfaces, procedures

PYLOT_ROOT_DIR = os.path.join(PROJECT_DIR, "src", "prfpylot")
SENSOR_DATA_CONTEXTS = [
    tum_esm_em27_metadata.types.SensorDataContext(
        sensor_id="so",
        serial_number=39,
        utc_offset=0.0,
        pressure_calibration_factor=1,
        date=date,
        location=tum_esm_em27_metadata.types.Location(
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
def test_so_container(wrap_test_with_mainlock, download_sample_data):

    config = custom_types.Config(
        **{
            "process_data_automatically": True,
            "data_filter": {
                "sensor_ids_to_consider": ["mc", "so"],
                "start_date": "20220101",
                "end_date": "20991231",
                "min_days_delay": 5,
            },
            "location_data": {
                "github_repository": "tum-esm/em27-location-data",
                "access_token": "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",
            },
            "data_src_dirs": {
                "datalogger": f"{PROJECT_DIR}/example/inputs/log",
                "vertical_profiles": f"{PROJECT_DIR}/example/inputs/map",
                "interferograms": f"{PROJECT_DIR}/example/inputs/ifg",
            },
            "data_dst_dirs": {"results": f"{PROJECT_DIR}/example/outputs"},
        }
    )

    # remove old containers
    for f in os.listdir(os.path.join(PYLOT_ROOT_DIR, "containers")):
        p = os.path.join(PYLOT_ROOT_DIR, "containers", f)
        if os.path.isdir(p) and (f != "main"):
            shutil.rmtree(p)

    # set up container
    logger = utils.Logger("pytest", print_only=True)
    pylot_factory = interfaces.PylotFactory(logger)
    session = procedures.create_session.run(pylot_factory, SENSOR_DATA_CONTEXTS[0])

    # run container
    procedures.process_session.run(config, session)

    # assert output correctness
    # TODO
