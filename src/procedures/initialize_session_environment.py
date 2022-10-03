import os
import shutil
from src import types

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(session: types.SessionDict) -> None:
    sensor = session["sensor"]
    lat = session["lat"]
    lon = session["lon"]
    alt = session["alt"]
    serial_number = session["serial_number"]
    utc_offset = session["utc_offset"]

    # Clear directories "inputs" and "outputs"
    for subdirectory in ["inputs", "outputs"]:
        shutil.rmtree(f"{PROJECT_DIR}/{subdirectory}")
        os.mkdir(f"{PROJECT_DIR}/{subdirectory}")
        os.system(f"touch {PROJECT_DIR}/{subdirectory}/.gitkeep")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_ifg")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_map")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_pressure")

    # Create YAML file for proffast
    with open(f"{PROJECT_DIR}/src/config/pylot_config_template.yml", "r") as f:
        file_content = "".join(f.readlines())

    replacements = {
        "SERIAL_NUMBER": str(serial_number).zfill(3),
        "SENSOR": sensor,
        "PROJECT_DIR": PROJECT_DIR,
        "COORDINATES_LAT": str(round(lat, 3)),
        "COORDINATES_LON": str(round(lon, 3)),
        "COORDINATES_ALT": str(round(alt / 1000.0, 3)),
        "UTC_OFFSET": str(round(utc_offset, 2)),
    }

    for key, value in replacements.items():
        file_content = file_content.replace(f"%{key}%", value)

    with open(f"{PROJECT_DIR}/inputs/{sensor}-pylot-config.yml", "w") as f:
        f.write(file_content)
