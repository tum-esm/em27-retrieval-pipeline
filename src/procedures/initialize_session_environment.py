import os
import shutil

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))


def run(config: dict, session):
    sensor = session["sensor"]
    lat = session["lat"]
    lon = session["lon"]
    alt = session["alt"]
    serial_number = session["serial_number"]

    # TODO: move these checks into config-load

    assert os.path.isfile(
        f"{PROJECT_DIR}/.venv/bin/python"
    ), "virtual environment does not exist"

    assert os.path.isfile(
        f"{PROJECT_DIR}/location-data/.gitignore"
    ), "please run fetch-location-data.py first"

    YAML_TEMPLATE = f"{PROJECT_DIR}/src/config/pylot_config_template.yml"

    assert os.path.isfile(
        f"{PROJECT_DIR}/src/prfpylot/prfpylot/pylot.py"
    ), f"submodule src/prfpylot not initialized"

    assert all(
        [
            os.path.isfile(x)
            for x in [
                f"{PROJECT_DIR}/src/prfpylot/prf/preprocess/preprocess4",
                f"{PROJECT_DIR}/src/prfpylot/prf/pcxs20",
                f"{PROJECT_DIR}/src/prfpylot/prf/invers20",
            ]
        ]
    ), f"proffast {config['proffastVersion']} is not fully compiled"

    # Clear directories "inputs" and "outputs"
    for _d in ["inputs", "outputs"]:
        shutil.rmtree(f"{PROJECT_DIR}/{_d}")
        os.mkdir(f"{PROJECT_DIR}/{_d}")
        os.system(f"touch {PROJECT_DIR}/{_d}/.gitkeep")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_ifg")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_map")
    os.mkdir(f"{PROJECT_DIR}/inputs/{sensor}_pressure")

    # Create YAML file for proffast
    with open(YAML_TEMPLATE, "r") as _f:
        file_content = "".join(_f.readlines())

    replacements = {
        "SERIAL_NUMBER": str(serial_number).zfill(3),
        "SENSOR": sensor,
        "PROJECT_DIR": PROJECT_DIR,
        "COORDINATES_LAT": str(round(lat, 3)),
        "COORDINATES_LON": str(round(lon, 3)),
        "COORDINATES_ALT": str(round(alt / 1000.0, 3)),
    }

    for key, value in replacements.items():
        file_content = file_content.replace(f"%{key}%", value)

    with open(f"{PROJECT_DIR}/inputs/{sensor}-pylot-config.yml", "w") as _f:
        _f.write(file_content)
