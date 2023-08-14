import json
import os
import sys
import click
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=5)
if os.path.basename(_PROJECT_DIR) != "em27-retrieval-pipeline":
    _PROJECT_DIR = os.path.dirname(_PROJECT_DIR)
sys.path.append(_PROJECT_DIR)

import create_input_files, execute_proffast, move_data
from src import custom_types


@click.command(help="Run proffast 1.0 for a given proffast session")
@click.argument("session_string", type=str)
def main(session_string: str) -> None:
    print("Parsing session string")
    try:
        session = custom_types.ProffastSession(**json.loads(session_string))
    except Exception as e:
        print("Invalid session string")
        raise e

    def log(msg: str) -> None:
        with open(os.path.join(session.ctn.data_output_path, "wrapper.log"), "a") as f:
            f.write(msg + "\n")

    log("preparing data")
    create_input_files.move_profiles_and_datalogger_files(session)

    log("creating preprocess input file")
    create_input_files.create_preprocess_input_file(session)
    log("run preprocess")
    execute_proffast.execute_preprocess(session, log)
    log("move BIN files")
    move_data.move_bin_files(session)

    log("creating pcxs input file")
    create_input_files.create_pcxs_input_file(session)
    log("run pcxs")
    execute_proffast.execute_pcxs(session, log)

    log("creating invers input file")
    create_input_files.create_invers_input_file(session)
    log("run invers")
    execute_proffast.execute_invers(session, log)
    log("merge invers output files")
    move_data.merge_output_files(session)

    log("done")


if __name__ == "__main__":
    main(prog_name="prf-1.0-wrapper")
