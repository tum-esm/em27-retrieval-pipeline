import os
from src import custom_types, utils

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def _insert_replacements(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(f"%{key}%", value)
    return content


def _generate_pylot_config(session: custom_types.Session) -> None:
    file_content = utils.load_file(
        f"{PROJECT_DIR}/src/config/pylot_config_template.yml"
    )
    replacements = {
        "SERIAL_NUMBER": str(session.serial_number).zfill(3),
        "SENSOR_ID": session.sensor_id,
        "PROJECT_DIR": PROJECT_DIR,
        "COORDINATES_LAT": str(round(session["lat"], 3)),
        "COORDINATES_LON": str(round(session["lon"], 3)),
        "COORDINATES_ALT": str(round(session["alt"] / 1000.0, 3)),
        "UTC_OFFSET": str(round(session["utc_offset"], 2)),
        "CONTAINER_ID": session.container_id,
        "PROFFAST_PATH": os.path.join(session.container_path, "prf"),
    }
    file_content = _insert_replacements(file_content, replacements)
    utils.dump_file(
        f"{PROJECT_DIR}/inputs/{session.container_id}/"
        + f"{session.sensor_id}-pylot-config.yml",
        file_content,
    )


def _generate_pylot_log_format(session: custom_types.Session) -> None:
    file_content = utils.load_file(
        f"{PROJECT_DIR}/src/config/pylot_log_format_template.yml"
    )
    replacements = {
        "SENSOR": session["sensor"],
        "UTC_OFFSET": str(round(session.utc_offset, 2)),
    }
    file_content = _insert_replacements(file_content, replacements)
    utils.dump_file(
        f"{PROJECT_DIR}/inputs/{session.container_id}/"
        + f"{session.sensor_id}-log-format.yml",
        file_content,
    )


def run(session: custom_types.SessionDict) -> None:
    for key in ["ifg", "map", "pressure"]:
        os.makedirs(
            f"{PROJECT_DIR}/inputs/{session.container_id}/"
            + f"{session.sensor_id}_{key}"
        )

    _generate_pylot_config(session)
    _generate_pylot_log_format(session)
