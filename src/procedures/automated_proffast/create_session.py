import os
import tum_esm_em27_metadata
from src import custom_types, interfaces
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_PYLOT_CONFIG_DIR = os.path.join(
    _PROJECT_DIR, "src/procedures/automated_proffast/pylot_src/config"
)


def _generate_pylot_config(session: custom_types.Session) -> None:
    file_content = tum_esm_utils.files.load_file(
        os.path.join(_PYLOT_CONFIG_DIR, "pylot_config_template.yml")
    )
    tum_esm_utils.files.dump_file(
        session.pylot_config_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SERIAL_NUMBER": str(session.serial_number).zfill(3),
                "SENSOR_ID": session.sensor_id,
                "COORDINATES_LAT": str(round(session.location.lat, 3)),
                "COORDINATES_LON": str(round(session.location.lon, 3)),
                "COORDINATES_ALT": str(round(session.location.alt / 1000.0, 3)),
                "UTC_OFFSET": str(round(session.utc_offset, 2)),
                "CONTAINER_ID": session.container_id,
                "CONTAINER_PATH": session.container_path,
                "DATA_INPUT_PATH": session.data_input_path,
                "DATA_OUTPUT_PATH": session.data_output_path,
                "PYLOT_LOG_FORMAT_PATH": session.pylot_log_format_path,
            },
        ),
    )


def _generate_pylot_log_format(session: custom_types.Session) -> None:
    file_content = tum_esm_utils.files.load_file(
        os.path.join(_PYLOT_CONFIG_DIR, "pylot_log_format_template.yml")
    )
    tum_esm_utils.files.dump_file(
        session.pylot_log_format_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SENSOR_ID": session.sensor_id,
                "UTC_OFFSET": str(round(session.utc_offset, 2)),
                "PRESSURE_CALIBRATION_FACTOR": str(
                    round(session.pressure_calibration_factor, 9)
                ),
                "PRESSURE_DATA_SOURCE": session.pressure_data_source,
            },
        ),
    )


def run(
    pylot_factory: interfaces.PylotFactory,
    sensor_data_context: tum_esm_em27_metadata.types.SensorDataContext,
) -> custom_types.Session:
    """Create a new container and the pylot config files"""
    new_container = pylot_factory.create_container()
    new_session = custom_types.Session(
        **sensor_data_context.dict(),
        **new_container.dict(),
    )

    _generate_pylot_config(new_session)
    _generate_pylot_log_format(new_session)

    return new_session
