import shutil
import pytest
import glob
import os
import sys
from tests.fixtures import wrap_test_with_mainlock, PROJECT_DIR

sys.path.append(os.path.join(PROJECT_DIR, "src", "prfpylot"))
from src.prfpylot.prfpylot.pylot import Pylot


def _set_up_empty_output_directory():
    output_dir = os.path.join(PROJECT_DIR, "example", "outputs")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)


def _load(path: str) -> str:
    with open(path, "r") as f:
        return "".join(f.readlines())


def _dump(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def _insert_replacements(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def _generate_pylot_config() -> str:
    file_content = _load(f"{PROJECT_DIR}/src/config/pylot_config_template.yml")
    replacements = {
        "%SERIAL_NUMBER%": "115",
        "%SENSOR%": "mc",
        "%PROJECT_DIR%/src": f"{PROJECT_DIR}/src",
        "%PROJECT_DIR%/inputs": f"{PROJECT_DIR}/example/inputs",
        "%PROJECT_DIR%/outputs": f"{PROJECT_DIR}/example/outputs",
        "%COORDINATES_LAT%": "48.148",
        "%COORDINATES_LON%": "16.438",
        "%COORDINATES_ALT%": "0.180",
        "%UTC_OFFSET%": "0",
    }
    file_content = _insert_replacements(file_content, replacements)
    file_path = f"{PROJECT_DIR}/example/inputs/mc-pylot-config.yml"
    _dump(file_path, file_content)

    return file_path


def _generate_pylot_log_format() -> None:
    file_content = _load(f"{PROJECT_DIR}/src/config/pylot_log_format_template.yml")
    replacements = {
        "%SENSOR%": "mc",
        "%UTC_OFFSET%": "0",
    }
    file_content = _insert_replacements(file_content, replacements)
    _dump(f"{PROJECT_DIR}/example/inputs/mc-log-format.yml", file_content)


def _assert_output_file_integrity():
    output_dir = f"{PROJECT_DIR}/example/outputs/mc_SN115_220602-220602"
    expected_output_files = [
        f"mc-pylot-config.yml",
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
            lambda f: len(glob.glob(f"{output_dir}/{f}")) == 0,
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
    _set_up_empty_output_directory()
    pylot_config_path = _generate_pylot_config()
    _generate_pylot_log_format()

    Pylot(pylot_config_path, logginglevel="info").run(n_processes=1)

    _assert_output_file_integrity()
