import json
import os
import tum_esm_utils
from src import types

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=4
)


def run(session: types.RetrievalSession, test_mode: bool = False) -> None:
    if test_mode:
        _create_mock_outputs(session)
        return

    if isinstance(session, types.Proffast1RetrievalSession):
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
    elif isinstance(session, types.Proffast2RetrievalSession):
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
                    session.retrieval_algorithm,
                    "run_pylot_container.py",
                ),
                session.ctn.container_id,
                session.ctn.pylot_config_path,
            ])
        )
    else:
        raise NotImplementedError(
            f"Retrieval session type {type(session)} not implemented"
        )


def _create_mock_outputs(session: types.RetrievalSession) -> None:
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")

    # create output directory
    output_dir: str
    if isinstance(session.ctn, types.Proffast10Container):
        output_dir = os.path.join(session.ctn.container_path, "prf", "out_fast")
    if isinstance(
        session.ctn,
        (types.Proffast22Container, types.Proffast23Container),
    ):
        output_dir = os.path.join(
            session.ctn.data_output_path, f"{session.ctx.sensor_id}_" +
            f"SN{str(session.ctx.serial_number).zfill(3)}_{date_string[2:]}-{date_string[2:]}"
        )
    os.makedirs(os.path.join(output_dir, "logfiles"), exist_ok=True)

    # list dummy files to be created
    filepaths: list[str] = []
    if isinstance(session.ctn, types.Proffast10Container):
        filepaths = [
            (f"{session.ctx.sensor_id}{date_string[2:]}-combined-invparms.csv"),
            (
                f"{session.ctx.sensor_id}{date_string[2:]}-combined-invparms.parquet"
            ),
            "logfiles/wrapper.log",
            "logfiles/preprocess4.log",
            "logfiles/pcxs10.log",
            "logfiles/invers10.log",
        ]
    if isinstance(
        session.ctn,
        (types.Proffast22Container, types.Proffast23Container),
    ):
        filepaths = [
            (
                f"comb_invparms_{session.ctx.sensor_id}_SN{str(session.ctx.serial_number).zfill(3)}"
                + f"_{date_string[2:]}-{date_string[2:]}.csv"
            ),
            "pylot_config.yml",
            "pylot_log_format.yml",
            "logfiles/preprocess_output.log",
            "logfiles/pcxs_output.log",
            "logfiles/inv_output.log",
        ]

    # create dummy files
    for filepath in filepaths:
        with open(os.path.join(output_dir, filepath), "w") as f:
            f.write("...")
