import datetime
import os
import em27_metadata
import tum_esm_utils
from src import retrieval
from src import types, utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)
_PYLOT_CONFIG_DIR = os.path.join(
    _PROJECT_DIR, "src", "retrieval", "algorithms", "proffast-2.2", "config"
)


def _generate_pylot22_config(session: types.RetrievalSession) -> None:
    assert isinstance(
        session.ctn,
        (types.Proffast22Container, types.Proffast23Container),
    )

    file_content = tum_esm_utils.files.load_file(
        os.path.join(_PYLOT_CONFIG_DIR, "pylot_config_template.yml")
    )
    tum_esm_utils.files.dump_file(
        session.ctn.pylot_config_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SERIAL_NUMBER":
                    str(session.ctx.serial_number).zfill(3),
                "SENSOR_ID":
                    session.ctx.sensor_id,
                "COORDINATES_LAT":
                    str(round(session.ctx.location.lat, 3)),
                "COORDINATES_LON":
                    str(round(session.ctx.location.lon, 3)),
                "COORDINATES_ALT":
                    str(round(session.ctx.location.alt / 1000.0, 3)),
                "UTC_OFFSET":
                    str(round(session.ctx.utc_offset, 2)),
                "CONTAINER_ID":
                    session.ctn.container_id,
                "CONTAINER_PATH":
                    session.ctn.container_path,
                "DATA_INPUT_PATH":
                    session.ctn.data_input_path,
                "DATA_OUTPUT_PATH":
                    session.ctn.data_output_path,
                "PYLOT_LOG_FORMAT_PATH":
                    session.ctn.pylot_log_format_path,
            },
        ),
    )


def _generate_pylot23_config(session: types.RetrievalSession) -> None:
    _generate_pylot22_config(session)


def _generate_pylot22_log_format(session: types.RetrievalSession) -> None:
    assert isinstance(
        session.ctn,
        (types.Proffast22Container, types.Proffast23Container),
    )

    file_content = tum_esm_utils.files.load_file(
        os.path.join(_PYLOT_CONFIG_DIR, "pylot_log_format_template.yml")
    )
    tum_esm_utils.files.dump_file(
        session.ctn.pylot_log_format_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SENSOR_ID":
                    session.ctx.sensor_id,
                "UTC_OFFSET":
                    str(round(session.ctx.utc_offset, 2)),
                "PRESSURE_CALIBRATION_FACTOR":
                    str(round(session.ctx.calibration_factors.pressure, 9)),
                "PRESSURE_DATA_SOURCE":
                    session.ctx.pressure_data_source,
            },
        ),
    )


def _generate_pylot23_log_format(session: types.RetrievalSession) -> None:
    _generate_pylot22_log_format(session)


def run(
    container_factory: retrieval.dispatching.container_factory.ContainerFactory,
    sensor_data_context: em27_metadata.types.SensorDataContext,
    retrieval_algorithm: types.RetrievalAlgorithm,
) -> types.RetrievalSession:
    """Create a new container and the pylot config files"""
    new_session = types.RetrievalSession(
        ctx=sensor_data_context,
        ctn=container_factory.create_container(
            retrieval_algorithm=retrieval_algorithm
        ),
    )
    retrieval.utils.retrieval_status.RetrievalStatusList.update_item(
        sensor_data_context.sensor_id,
        sensor_data_context.from_datetime,
        container_id=new_session.ctn.container_id,
        process_start_time=datetime.datetime.utcnow(),
    )

    if isinstance(new_session.ctn, types.Proffast22Container):
        _generate_pylot22_config(new_session)
        _generate_pylot22_log_format(new_session)

    if isinstance(new_session.ctn, types.Proffast23Container):
        _generate_pylot23_config(new_session)
        _generate_pylot23_log_format(new_session)

    return new_session
