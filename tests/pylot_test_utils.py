import os
import sys
import shutil
import filelock
import pytest

dir = os.path.dirname
PROJECT_DIR = dir(dir(os.path.abspath(__file__)))
lock = filelock.FileLock(os.path.join(PROJECT_DIR, "src", "main.lock"), timeout=0)

sys.path.append(os.path.join(PROJECT_DIR, "src", "prfpylot"))
from src.prfpylot.prfpylot.pylot import Pylot


def _clean_output_directory():
    output_dir = os.path.join(PROJECT_DIR, "example", "pylot_outputs")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)


def _write_pylot_config():
    yaml_src = f"{PROJECT_DIR}/src/config/pylot_config_template.yml"
    yaml_dst = f"{PROJECT_DIR}/example/pylot_config.yml"
    with open(yaml_src, "r") as f:
        yaml_content = "".join(f.readlines())
    replacements = {
        "%PROJECT_DIR%/src": f"{PROJECT_DIR}/src",
        "%PROJECT_DIR%/inputs": f"{PROJECT_DIR}/example",
        "%PROJECT_DIR%/outputs": f"{PROJECT_DIR}/example/pylot_outputs",
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


def _assert_output_file_integrity():
    # FIXME: Update "logfiles/pcsx_output.log" to "logfiles/pcxs_output.log" once fixed
    output_dir = f"{PROJECT_DIR}/example/pylot_outputs/mc_SN115_20220602_20220602"
    for output_file in [
        f"pylot_config.yml",
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


def run_pylot_test():
    _clean_output_directory()
    pylot_config_file = _write_pylot_config()

    Pylot(pylot_config_file, logginglevel="info").run(n_processes=1)

    _assert_output_file_integrity()
