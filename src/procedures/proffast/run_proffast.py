import os
from src import custom_types
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)


def run(
    session: custom_types.ProffastSession,
) -> None:
    if isinstance(session.ctn, custom_types.Proffast22Container):
        tum_esm_utils.shell.run_shell_command(
            " ".join(
                [
                    os.path.join(
                        _PROJECT_DIR,
                        ".venv",
                        "bin",
                        "python",
                    ),
                    os.path.join(
                        _PROJECT_DIR,
                        "src",
                        "retrieval",
                        "proffast-2.2",
                        "run_pylot_container.py",
                    ),
                    session.ctn.container_id,
                    session.ctn.pylot_config_path,
                ]
            )
        )
    else:
        raise NotImplementedError()
