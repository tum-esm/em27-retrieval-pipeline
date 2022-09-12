import shutil
import pytest
import glob
import os
import sys
from tests.fixtures import wrap_test_with_mainlock, PROJECT_DIR

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
    output_dir = f"{PROJECT_DIR}/example/pylot_outputs/mc_SN115_220602-220602"
    expected_output_files = [
        f"pylot_config.yml",
        "input_files/preprocess4mc_220602.inp",
        "input_files/pcxs20mc_220602.inp",
        "input_files/invers20mc_220602_a.inp",
        "logfiles/preprocess_output.log",
        "logfiles/pcxs_output.log",
        "logfiles/inv_output.log",
        "logfiles/pylot_*.log",
        "comb_invparms_mc_SN115_220602-220602.csv",
    ]
    missing_output_files = list(
        filter(
            lambda f: len(glob.glob(f"{output_dir}/{f}")) == 1,
            expected_output_files,
        )
    )

    assert len(missing_output_files) == 0, (
        f"Missing {len(missing_output_files)}/{len(expected_output_files)}"
        + f" output files: {missing_output_files}"
    )

    with open(f"{output_dir}/comb_invparms_mc_SN115_220602-220602.csv", "r") as f:
        result_line_count = len(f.readlines())
        assert result_line_count > 2, "Output comb_invparms_*.csv is empty"


@pytest.mark.integration
def test_pylot(wrap_test_with_mainlock):
    _clean_output_directory()
    pylot_config_file = _write_pylot_config()

    Pylot(pylot_config_file, logginglevel="info").run(n_processes=1)

    _assert_output_file_integrity()
