import os
from src import custom_types, interfaces, utils

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


def _generate_pylot_config(session: custom_types.Session) -> None:
    file_content = utils.load_file(
        f"{PROJECT_DIR}/src/config/pylot_config_template.yml"
    )
    file_content = utils.insert_replacements(
        file_content,
        {
            "SERIAL_NUMBER": str(session.serial_number).zfill(3),
            "SENSOR_ID": session.sensor_id,
            "COORDINATES_LAT": str(round(session["lat"], 3)),
            "COORDINATES_LON": str(round(session["lon"], 3)),
            "COORDINATES_ALT": str(round(session["alt"] / 1000.0, 3)),
            "UTC_OFFSET": str(round(session["utc_offset"], 2)),
            "CONTAINER_ID": session.pylot_container.container_id,
            "CONTAINER_PATH": session.pylot_container.container_path,
            "DATA_INPUT_PATH": session.pylot_container.data_input_path,
            "DATA_OUTPUT_PATH": session.pylot_container.data_output_path,
            "PYLOT_LOG_FORMAT_PATH": session.pylot_container.pylot_log_format_path,
        },
    )
    utils.dump_file(
        session.pylot_container.pylot_config_path,
        file_content,
    )


def _generate_pylot_log_format(session: custom_types.Session) -> None:
    file_content = utils.load_file(
        f"{PROJECT_DIR}/src/config/pylot_log_format_template.yml"
    )
    file_content = utils.insert_replacements(
        file_content,
        {
            "SENSOR": session["sensor"],
            "UTC_OFFSET": str(round(session.utc_offset, 2)),
        },
    )
    utils.dump_file(
        session.pylot_container.pylot_log_format_path,
        file_content,
    )


def run(
    pylot_factory: interfaces.PylotFactory,
    sensor_data_context: custom_types.SensorDataContext,
) -> custom_types.Session:
    """Create a new container and the pylot config files"""

    new_container = pylot_factory.create_container()

    new_session = custom_types.Session(
        sensor_data_context=sensor_data_context,
        container=new_container,
    )

    _generate_pylot_config(new_session)
    _generate_pylot_log_format(new_session)

    return new_session
