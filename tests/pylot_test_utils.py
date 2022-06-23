import os
import sys
import shutil
import filelock
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
LOCK_FILE = f"{PROJECT_DIR}/src/main.lock"
lock = filelock.FileLock(LOCK_FILE, timeout=0)


def clean_output_directory(pylot_slug: str):
    output_dir = f"{PROJECT_DIR}/example/{pylot_slug}_outputs"
    for f in os.listdir(output_dir):
        if os.path.isdir(f"{output_dir}/{f}"):
            shutil.rmtree(f"{output_dir}/{f}")


def _write_pylot_config(pylot_slug: str):
    yaml_src = f"{PROJECT_DIR}/src/config/{pylot_slug}_config_template.yml"
    yaml_dst = f"{PROJECT_DIR}/example/{pylot_slug}_config.yml"
    with open(yaml_src, "r") as f:
        yaml_content = "".join(f.readlines())
    replacements = {
        "%PROJECT_DIR%/src": f"{PROJECT_DIR}/src",
        "%PROJECT_DIR%/inputs": f"{PROJECT_DIR}/example",
        "%PROJECT_DIR%/outputs": f"{PROJECT_DIR}/example/{pylot_slug}_outputs",
        "%SERIAL_NUMBER%": "115",
        "%SENSOR%": "mc",
        "%COORDINATES_LAT%": "48.148",
        "%COORDINATES_LON%": "16.438",
        "%COORDINATES_ALT%": "0.18",
    }
    for r_from, r_to in replacements.items():
        yaml_content = yaml_content.replace(r_from, r_to)
    with open(yaml_dst, "w") as f:
        f.write(yaml_content)

    return yaml_dst


def _assert_output_file_integrity(pylot_slug: str):
    # FIXME: Update "logfiles/pcsx_output.log" to "logfiles/pcxs_output.log" once fixed
    output_dir = (
        f"{PROJECT_DIR}/example/{pylot_slug}_outputs/mc_SN115_20220602_20220602"
    )
    for output_file in [
        f"{pylot_slug}_config.yml",
        "input_files/preprocess4mc_220602.inp",
        "input_files/pcxs20mc_220602.inp",
        "input_files/invers20mc_220602.inp",
        "logfiles/GeneralLogfile.log",
        "logfiles/preprocess_output.log",
        "logfiles/pcsx_output.log",
        "logfiles/inv_output.log",
        "combined_invparms_mc_20220602-20220602.csv",
    ]:
        f = f"{output_dir}/{output_file}"
        assert os.path.isfile(f), f"{f} does not exist"

    with open(f"{output_dir}/combined_invparms_mc_20220602-20220602.csv", "r") as f:
        result_line_count = len(f.readlines())
        assert result_line_count > 2


@pytest.fixture
def wrap_test_with_mainlock():
    try:
        lock.acquire()
        yield
        lock.release()
    except filelock.Timeout:
        raise Exception("automation is already running")


def run_pylot_test(pylot_slug: str):
    clean_output_directory(pylot_slug)
    pylot_config_file = _write_pylot_config(pylot_slug)

    sys.path.append(f"{PROJECT_DIR}/src/{pylot_slug}")
    if pylot_slug == "pylot_1_0":
        from src.pylot_1_0.prfpylot.pylot import Pylot
    if pylot_slug == "pylot_1_1":
        from src.pylot_1_1.prfpylot.pylot import Pylot

    Pylot(pylot_config_file, logginglevel="info").run(n_processes=1)

    _assert_output_file_integrity(pylot_slug)
