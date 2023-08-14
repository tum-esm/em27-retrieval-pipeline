import json
import sys
import click
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=6)
sys.path.append(_PROJECT_DIR)

import create_input_files, execute_proffast, move_data
from src import custom_types


@click.command(help="Run proffast 1.0 for a given proffast session")
@click.argument("session_string", type=str)
def main(session_string: str) -> None:
    try:
        session = custom_types.ProffastSession(**json.loads(session_string))
    except Exception as e:
        print("Invalid session string")
        raise e

    # prepare data
    create_input_files.move_profiles_and_datalogger_files(session)

    # create preprocess input file, run preprocess, move BIN files
    create_input_files.create_preprocess_input_file(session)
    execute_proffast.execute_preprocess(session)
    move_data.move_bin_files(session)

    # create pcxs input file and run pcxs
    create_input_files.create_pcxs_input_file(session)
    execute_proffast.execute_pcxs(session)

    # create invers input file, run invers, merge invers outputs
    create_input_files.create_invers_input_file(session)
    execute_proffast.execute_invers(session)
    move_data.merge_output_files(session)


if __name__ == "__main__":
    main(prog_name="prfpylot-1.0-cli")
