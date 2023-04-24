import os
from src import custom_types, utils
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)


def run(
    pylot_session: custom_types.PylotSession,
    logger: utils.automated_proffast.Logger,
) -> None:
    tum_esm_utils.shell.run_shell_command(
        command=" ".join(
            [
                os.path.join(
                    _PROJECT_DIR,
                    ".venv",
                    "bin",
                    "python",
                ),
                os.path.join(
                    _PROJECT_DIR, "src", "pylot_src", "run_pylot_container.py"
                ),
                pylot_session.container_id,
                pylot_session.pylot_config_path,
            ]
        )
    )
