import os
import shutil
import subprocess


dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
YAML_TEMPLATE = f"{PROJECT_DIR}/src/pylot_config_template.yml"


def run(session):
    session_sensor = session["sensor"]
    session_lat = session["lat"]
    session_lon = session["lon"]
    session_alt = session["alt"]
    session_serial_number = session["serial_number"]

    assert os.path.isfile(
        f"{PROJECT_DIR}/.venv/bin/python"
    ), "Virtual environment does not exist"

    assert os.path.isfile(
        f"{PROJECT_DIR}/download-map-data/run.py"
    ), "Module download-map-data not initialized"

    assert os.path.isfile(
        f"{PROJECT_DIR}/proffastpylot/prfpylot/pylot.py"
    ), "Module proffastpylot not initialized"

    assert all(
        [
            os.path.isfile(x)
            for x in [
                f"{PROJECT_DIR}/proffastpylot/prf/preprocess/preprocess4",
                f"{PROJECT_DIR}/proffastpylot/prf/pcxs20",
                f"{PROJECT_DIR}/proffastpylot/prf/invers20",
            ]
        ]
    ), "PROFFAST not compiled completely"

    # Clear directories "inputs" and "outputs"
    for _d in ["inputs", "outputs"]:
        shutil.rmtree(f"{PROJECT_DIR}/{_d}")
        os.mkdir(f"{PROJECT_DIR}/{_d}")
        os.system(f"touch {PROJECT_DIR}/{_d}/.gitkeep")
    os.mkdir(f"{PROJECT_DIR}/inputs/{session_sensor}_ifg")
    os.mkdir(f"{PROJECT_DIR}/inputs/{session_sensor}_map")
    os.mkdir(f"{PROJECT_DIR}/inputs/{session_sensor}_pressure")

    # Create 'coords.csv' file
    with open(f"{PROJECT_DIR}/inputs/coords.csv", "w") as _f:
        _f.write("Site, Latitude, Longitude, Altitude_kmasl, Starttime\n")
        _f.write(
            ", ".join(
                [
                    session_sensor,
                    str(round(session_lat, 3)),
                    str(round(session_lon, 3)),
                    str(round(session_alt / 1000.0, 3)),
                    "2015-01-01",
                ]
            )
            + "\n"
        )

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
    }

    for key, value in replacements.items():
        file_content = file_content.replace(f"%{key}%", value)

    with open(f"{PROJECT_DIR}/inputs/{session_sensor}-pylot-config.yml", "w") as _f:
        _f.write(file_content)
