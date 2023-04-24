import os
import tum_esm_em27_metadata
from src import custom_types, interfaces
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_PYLOT_CONFIG_DIR = os.path.join(_PROJECT_DIR, "src", "pylot_src", "config")


def _generate_pylot_config(pylot_session: custom_types.PylotSession) -> None:
    file_content = tum_esm_utils.files.load_file(
        os.path.join(_PYLOT_CONFIG_DIR, "pylot_config_template.yml")
    )
    tum_esm_utils.files.dump_file(
        pylot_session.pylot_config_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SERIAL_NUMBER": str(pylot_session.serial_number).zfill(3),
                "SENSOR_ID": pylot_session.sensor_id,
                "COORDINATES_LAT": str(round(pylot_session.location.lat, 3)),
                "COORDINATES_LON": str(round(pylot_session.location.lon, 3)),
                "COORDINATES_ALT": str(round(pylot_session.location.alt / 1000.0, 3)),
                "UTC_OFFSET": str(round(pylot_session.utc_offset, 2)),
                "CONTAINER_ID": pylot_session.container_id,
                "CONTAINER_PATH": pylot_session.container_path,
                "DATA_INPUT_PATH": pylot_session.data_input_path,
                "DATA_OUTPUT_PATH": pylot_session.data_output_path,
                "PYLOT_LOG_FORMAT_PATH": pylot_session.pylot_log_format_path,
            },
        ),
    )


def _generate_pylot_log_format(pylot_session: custom_types.PylotSession) -> None:
    file_content = tum_esm_utils.files.load_file(
        os.path.join(_PYLOT_CONFIG_DIR, "pylot_log_format_template.yml")
    )
    tum_esm_utils.files.dump_file(
        pylot_session.pylot_log_format_path,
        tum_esm_utils.text.insert_replacements(
            file_content,
            {
                "SENSOR_ID": pylot_session.sensor_id,
                "UTC_OFFSET": str(round(pylot_session.utc_offset, 2)),
                "PRESSURE_CALIBRATION_FACTOR": str(
                    round(pylot_session.pressure_calibration_factor, 9)
                ),
                "PRESSURE_DATA_SOURCE": pylot_session.pressure_data_source,
            },
        ),
    )


def run(
    pylot_factory: interfaces.automated_proffast.PylotFactory,
    sensor_data_context: tum_esm_em27_metadata.types.SensorDataContext,
) -> custom_types.PylotSession:
    """Create a new container and the pylot config files"""
    new_container = pylot_factory.create_container()
    new_session = custom_types.PylotSession(
        **sensor_data_context.dict(),
        **new_container.dict(),
    )

    _generate_pylot_config(new_session)
    _generate_pylot_log_format(new_session)

    return new_session
