"""Ths script bundles the raw output files of the Proffast Pylot into a single tarball."""

import os
import sys
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
sys.path.append(PROJECT_DIR)

from src.utils import utils

if __name__ == "__main__":
    config = utils.load_config()
    logger = utils.Logger("development", print_only=True)
    logger.info("starting to bundle output files")

    # strip away any trailing slash from output dir path
    output_dir = "/" + config.data_dst_dirs.results.strip("/")
    output_dir_name = output_dir.split("/")[-1]
    logger.info(f'using output directory "{output_dir}"')

    bundle_file = output_dir + "-bundle.tar"
    logger.info(f'writing outputs to bundle file "{bundle_file}"')
    if os.path.exists(bundle_file):
        logger.warning(f"stopping because output file exists, stopping now")

    tum_esm_utils.shell.run_shell_command(
        command=(
            f"find  {output_dir_name}/ " +
            f'-wholename "{output_dir_name}/m?/*2.2*/*/????????/about.json" -o '
            +
            f'-wholename "{output_dir_name}/m?/*2.2*/*/????????/automation.log" -o '
            +
            f'-wholename "{output_dir_name}/m?/*2.2*/*/????????/comb_*.csv" ' +
            f"| tar -cvf {bundle_file} --files-from -"
        ),
        working_directory=os.path.dirname(output_dir),
    )
    logger.info("✨ done ✨")
