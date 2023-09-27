import os
import tum_esm_em27_metadata
from src import retrieval, utils
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)
_PYLOT_CONFIG_DIR = os.path.join(
    _PROJECT_DIR, "src", "retrieval", "algorithms", "proffast-2.2", "config"
)


def _generate_pylot22_config(session: utils.types.RetrievalSession) -> None:
    assert isinstance(
        session.ctn,
        (utils.types.Proffast22Container, utils.types.Proffast23Container),
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


def _generate_pylot23_config(session: utils.types.RetrievalSession) -> None:
    _generate_pylot22_config(session)


def _generate_pylot22_log_format(session: utils.types.RetrievalSession) -> None:
    assert isinstance(
        session.ctn,
        (utils.types.Proffast22Container, utils.types.Proffast23Container),
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
                    str(round(session.ctx.pressure_calibration_factor, 9)),
                "PRESSURE_DATA_SOURCE":
                    session.ctx.pressure_data_source,
            },
        ),
    )


def _generate_pylot23_log_format(session: utils.types.RetrievalSession) -> None:
    _generate_pylot22_log_format(session)


def run(
    container_factory: retrieval.dispatching.container_factory.ContainerFactory,
    sensor_data_context: tum_esm_em27_metadata.types.SensorDataContext,
) -> utils.types.RetrievalSession:
    """Create a new container and the pylot config files"""
    new_session = utils.types.RetrievalSession(
        ctx=sensor_data_context,
        ctn=container_factory.create_container(),
    )

    if isinstance(new_session.ctn, utils.types.Proffast22Container):
        _generate_pylot22_config(new_session)
        _generate_pylot22_log_format(new_session)

    if isinstance(new_session.ctn, utils.types.Proffast23Container):
        _generate_pylot23_config(new_session)
        _generate_pylot23_log_format(new_session)

    return new_session
