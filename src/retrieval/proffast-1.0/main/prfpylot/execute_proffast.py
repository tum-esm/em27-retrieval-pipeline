import datetime
import os
from typing import Callable
import tum_esm_utils
from src import custom_types


def execute_preprocess(
    session: custom_types.ProffastSession, log: Callable[[str], None]
) -> None:
    prf_dir = os.path.join(session.ctn.container_path, "prf")
    start_timestamp = datetime.datetime.utcnow().timestamp()

    # running preprocess
    tum_esm_utils.shell.run_shell_command(
        f"./preprocess4 > {session.ctn.data_output_path}/preprocess4.log",
        working_directory=os.path.join(prf_dir, "preprocess"),
    )

    end_timestamp = datetime.datetime.utcnow().timestamp()
    time_taken = round(end_timestamp - start_timestamp, 6)
    log(f"finished preprocess (took {time_taken} seconds)")


def execute_pcxs(
    session: custom_types.ProffastSession, log: Callable[[str], None]
) -> None:
    prf_dir = os.path.join(session.ctn.container_path, "prf")
    start_timestamp = datetime.datetime.utcnow().timestamp()

    # running pcxs10
    tum_esm_utils.shell.run_shell_command(
        f"./pcxs10 pcxs10.inp > {session.ctn.data_output_path}/pcxs10.log",
        working_directory=prf_dir,
    )

    # renaming output files
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    if os.path.isfile(
        f"{prf_dir}/wrk_fast/{session.ctx.sensor_id}{date_string[:6]}-abscos.bin"
    ):
        os.rename(
            f"{prf_dir}/wrk_fast/{session.ctx.sensor_id}{date_string[:6]}-abscos.bin",
            f"{prf_dir}/wrk_fast/{session.ctx.sensor_id}{date_string}-abscos.bin",
        )
    if os.path.isfile(
        f"{prf_dir}/out_fast/{session.ctx.sensor_id}{date_string[:6]}-colsens.dat"
    ):
        os.rename(
            f"{prf_dir}/out_fast/{session.ctx.sensor_id}{date_string[:6]}-colsens.dat",
            f"{prf_dir}/out_fast/{session.ctx.sensor_id}{date_string}-colsens.dat",
        )

    end_timestamp = datetime.datetime.utcnow().timestamp()
    time_taken = round(end_timestamp - start_timestamp, 6)
    log(f"finished pcxs10 (took {time_taken} seconds)")


def execute_invers(
    session: custom_types.ProffastSession, log: Callable[[str], None]
) -> None:
    prf_dir = os.path.join(session.ctn.container_path, "prf")
    start_timestamp = datetime.datetime.utcnow().timestamp()

    # running invers10
    tum_esm_utils.shell.run_shell_command(
        'printf "Y\n%.0s" {1..100} | ./invers10 invers10.inp'
        + f" > {session.ctn.data_output_path}/invers10.log",
        working_directory=prf_dir,
    )

    # renaming output files
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    for f in os.listdir(f"{prf_dir}/out_fast"):
        if date_string not in f:
            os.rename(
                f"{prf_dir}/out_fast/{f}",
                f"{prf_dir}/out_fast/{f.replace(date_string[:6], date_string)}",
            )

    end_timestamp = datetime.datetime.utcnow().timestamp()
    time_taken = round(end_timestamp - start_timestamp, 6)
    log(f"finished invers10 (took {time_taken} seconds)")
