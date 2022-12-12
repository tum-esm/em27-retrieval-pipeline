import os
import shutil
from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def _load(path: str) -> str:
    with open(path, "r") as f:
        return "".join(f.readlines())


def _dump(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def _insert_replacements(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(f"%{key}%", value)
    return content


def _generate_pylot_config(session: types.SessionDict, container_path: str, container_id: str) -> None:
    file_content = _load(f"{PROJECT_DIR}/src/config/pylot_config_template.yml")
    replacements = {
        "SERIAL_NUMBER": str(session["serial_number"]).zfill(3),
        "SENSOR": session["sensor"],
        "PROJECT_DIR": PROJECT_DIR,
        "COORDINATES_LAT": str(round(session["lat"], 3)),
        "COORDINATES_LON": str(round(session["lon"], 3)),
        "COORDINATES_ALT": str(round(session["alt"] / 1000.0, 3)),
        "UTC_OFFSET": str(round(session["utc_offset"], 2)),
        "PROFFAST_PATH": container_path
    }
    file_content = _insert_replacements(file_content, replacements)
    _dump(f"{PROJECT_DIR}/inputs/{container_id}/{session['sensor']}-pylot-config.yml", file_content)


def _generate_pylot_log_format(session: types.SessionDict, container_id: str) -> None:
    file_content = _load(f"{PROJECT_DIR}/src/config/pylot_log_format_template.yml")
    replacements = {
        "SENSOR": session["sensor"],
        "UTC_OFFSET": str(round(session["utc_offset"], 2)),
    }
    file_content = _insert_replacements(file_content, replacements)
    _dump(f"{PROJECT_DIR}/inputs/{container_id}/{session['sensor']}-log-format.yml", file_content)


def run(session: types.SessionDict) -> None:
    container_id = session['container_id']
    container_path = session["container_path"] 

    os.makedirs(f"{PROJECT_DIR}/inputs/{container_id}/{session['sensor']}_ifg")
    os.makedirs(f"{PROJECT_DIR}/inputs/{container_id}/{session['sensor']}_map")
    os.mkdirs(f"{PROJECT_DIR}/inputs/{container_id}/{session['sensor']}_pressure")

    _generate_pylot_config(session=session, container_id=container_id, container_path=container_path)
    _generate_pylot_log_format(session)
