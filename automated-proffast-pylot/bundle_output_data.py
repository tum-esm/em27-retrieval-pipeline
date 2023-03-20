import os
import tum_esm_utils
from src import utils


def run():
    config = utils.load_config()
    logger = utils.Logger("development", print_only=True)
    logger.info("starting to bundle output files")

    # strip away any trailing slash from output dir path
    output_dir = config.data_dst_dirs.results
    output_dir = output_dir[:-1] if (output_dir[-1] == "/") else output_dir
    output_dir_name = output_dir.split("/")[-1]
    logger.info(f'using output directory "{output_dir}"')

    bundle_file = output_dir + "-bundle.tar"
    logger.info(f'writing outputs to bundle file "{bundle_file}"')
    if os.path.exists(bundle_file):
        logger.warning(f"stopping because output file exists, stopping now")

    tum_esm_utils.shell.run_shell_command(
        command=(
            f"find  {output_dir_name}/ "
            + f'-wholename "{output_dir_name}/m?/*2.2*/*/????????/about.json" -o '
            + f'-wholename "{output_dir_name}/m?/*2.2*/*/????????/automation.log" -o '
            + f'-wholename "{output_dir_name}/m?/*2.2*/*/????????/comb_*.csv" '
            + f"| tar -cvf {bundle_file} --files-from -"
        ),
        working_directory=os.path.dirname(output_dir),
    )
    logger.info("✨ done ✨")


if __name__ == "__main__":
    run()
