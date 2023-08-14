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

    # create preprocess input file
    procedures.create_input_files.create_preprocess_input_file(session)

    # run preprocess

    # create pcxs input file
    procedures.create_input_files.create_pcxs_input_file(session)

    # run pcxs

    # create invers input file
    procedures.create_input_files.create_invers_input_file(session)

    # run invers

    # merge invers outputs

    pass


if __name__ == "__main__":
    main(prog_name="prfpylot-1.0-cli")
