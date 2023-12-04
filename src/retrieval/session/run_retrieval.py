import json
import os
import tum_esm_utils
from src import types

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)


def run(session: types.RetrievalSession, ) -> None:
    if isinstance(session.ctn, types.Proffast10Container):
        tum_esm_utils.shell.run_shell_command(
            " ".join([
                os.path.join(
                    _PROJECT_DIR,
                    ".venv",
                    "bin",
                    "python",
                ),
                os.path.join(
                    session.ctn.container_path,
                    "prfpylot",
                    "main.py",
                ),
                '"' + json.dumps(session.model_dump()).replace('"', '\\"') +
                '"',
            ])
        )

    if isinstance(
        session.ctn,
        (types.Proffast22Container, types.Proffast23Container),
    ):
        tum_esm_utils.shell.run_shell_command(
            " ".join([
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
                    "algorithms",
                    (
                        "proffast-2.2"
                        if isinstance(session.ctn, types.Proffast22Container)
                        else "proffast-2.3"
                    ),
                    "run_pylot_container.py",
                ),
                session.ctn.container_id,
                session.ctn.pylot_config_path,
            ])
        )
