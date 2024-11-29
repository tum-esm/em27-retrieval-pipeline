import os
import sys
import click
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=5)
pyproj_file = os.path.join(_PROJECT_DIR, "pyproject.toml")
assert os.path.isfile(pyproj_file), f"{_PROJECT_DIR} does not seem to be the root of the project"
with open(pyproj_file, "r") as f:
    assert 'name = "em27-retrieval-pipeline"' in f.read(
    ), f"{_PROJECT_DIR} does not seem to be the root of the project"
sys.path.append(_PROJECT_DIR)

import create_input_files
import execute_proffast
import move_data
from src import types

_CONTAINER_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
_LOGS_DIR = os.path.join(_CONTAINER_DIR, "prf", "out_fast", "logfiles")


def _log(msg: str) -> None:
    with open(os.path.join(_LOGS_DIR, "wrapper.log"), "a") as f:
        f.write(msg + "\n")


@click.command(help="Run proffast 1.0 for a given proffast session")
@click.argument("session_string", type=str)
def main(session_string: str) -> None:
    os.makedirs(_LOGS_DIR, exist_ok=True)

    _log("Parsing session string")
    try:
        session = types.Proffast1RetrievalSession.model_validate_json(session_string)
    except Exception as e:
        _log("Invalid session string")
        raise e

    _log("preparing data")
    create_input_files.move_profiles_and_ground_pressure_files(session)

    _log("creating preprocess input file")
    create_input_files.create_preprocess_input_file(session)
    _log("run preprocess")
    execute_proffast.execute_preprocess(session, _log)
    _log("move BIN files")
    move_data.move_bin_files(session)

    _log("creating pcxs input file")
    create_input_files.create_pcxs_input_file(session)
    _log("run pcxs")
    execute_proffast.execute_pcxs(session, _log)

    _log("creating invers input file")
    create_input_files.create_invers_input_file(session)
    _log("run invers")
    execute_proffast.execute_invers(session, _log)
    _log("merge invers output files")
    move_data.merge_output_files(session)

    _log("done")


if __name__ == "__main__":
    main(prog_name="prf-1.0-wrapper")
