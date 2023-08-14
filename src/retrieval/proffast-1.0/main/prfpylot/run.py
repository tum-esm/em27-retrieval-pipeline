import json
import sys
import click
import tum_esm_utils
import procedures

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=6)
sys.path.append(_PROJECT_DIR)

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
    procedures.create_input_files.move_profiles_and_datalogger_files(session)

    # create preprocess input file, run preprocess, move BIN files
    procedures.create_input_files.create_preprocess_input_file(session)
    procedures.run_proffast.run_preprocess(session)
    procedures.move_data.move_bin_files(session)

    # create pcxs input file and run pcxs
    procedures.create_input_files.create_pcxs_input_file(session)
    procedures.run_proffast.run_pcxs(session)

    # create invers input file, run invers, merge invers outputs
    procedures.create_input_files.create_invers_input_file(session)
    procedures.run_proffast.run_invers(session)
    procedures.move_data.merge_output_files(session)


if __name__ == "__main__":
    main(prog_name="prfpylot-1.0-cli")
