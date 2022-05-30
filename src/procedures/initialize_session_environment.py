import os
import shutil
import subprocess
from src.utils import load_setup

PROJECT_DIR, CONFIG = load_setup()
YAML_TEMPLATE = f"{PROJECT_DIR}/src/pylot_config_template.yml"


def run(session):
    session_sensor = session["sensor"]
    session_lat = session["lat"]
    session_lon = session["lon"]
    session_alt = session["alt"]
    session_serial_number = session["serial_number"]

    assert os.path.isfile(
        f"{PROJECT_DIR}/.venv/bin/python"
    ), "virtual environment does not exist"

    assert os.path.isfile(
        f"{PROJECT_DIR}/location-data/.gitignore"
    ), "module location-data not initialized"

    assert os.path.isfile(
        f"{PROJECT_DIR}/src/pylot/prfpylot/pylot.py"
    ), "module proffastpylot not initialized"

    assert all(
        [
            os.path.isfile(x)
            for x in [
                f"{PROJECT_DIR}/src/pylot/prf/preprocess/preprocess4",
                f"{PROJECT_DIR}/src/pylot/prf/pcxs20",
                f"{PROJECT_DIR}/src/pylot/prf/invers20",
            ]
        ]
    ), "proffast is not compiled completely"

    # Clear directories "inputs" and "outputs"
    for _d in ["inputs", "outputs"]:
        shutil.rmtree(f"{PROJECT_DIR}/{_d}")
        os.mkdir(f"{PROJECT_DIR}/{_d}")
        os.system(f"touch {PROJECT_DIR}/{_d}/.gitkeep")
    os.mkdir(f"{PROJECT_DIR}/inputs/{session_sensor}_ifg")
    os.mkdir(f"{PROJECT_DIR}/inputs/{session_sensor}_map")
    os.mkdir(f"{PROJECT_DIR}/inputs/{session_sensor}_pressure")

    # Create YAML file for proffast
    with open(YAML_TEMPLATE, "r") as _f:
        file_content = "".join(_f.readlines())

    replacements = {
        "SERIAL_NUMBER": str(session_serial_number).zfill(3),
        "SENSOR": session_sensor,
        "PROJECT_DIR": PROJECT_DIR,
        "COMMIT_SHA": subprocess.check_output(
            ["git", "rev-parse", "--short", "--verify", "HEAD"]
        )
        .decode()
        .replace("\n", ""),
        "COORDINATES_LAT": str(round(session_lat, 3)),
        "COORDINATES_LON": str(round(session_lon, 3)),
        "COORDINATES_ALT": str(round(session_alt / 1000.0, 3)),
    }

    for key, value in replacements.items():
        file_content = file_content.replace(f"%{key}%", value)

    with open(f"{PROJECT_DIR}/inputs/{session_sensor}-pylot-config.yml", "w") as _f:
        _f.write(file_content)
