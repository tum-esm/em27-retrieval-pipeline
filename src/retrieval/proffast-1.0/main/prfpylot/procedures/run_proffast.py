import datetime
import os
import tum_esm_utils
from src import custom_types


def run_preprocess(session: custom_types.ProffastSession) -> None:
    prf_dir = os.path.join(session.ctn.container_path, "prf")
    start_timestamp = datetime.datetime.utcnow().timestamp()
    print("PREPROCESS: STARTING")

    # running preprocess
    stdout = tum_esm_utils.shell.run_shell_command(
        "./preprocess4 " + os.path.join(prf_dir, "preprocess", "preprocess4.inp"),
        working_directory=os.path.join(prf_dir, "preprocess"),
    )
    print(f"stdout:\n{stdout}")

    end_timestamp = datetime.datetime.utcnow().timestamp()
    time_taken = round(end_timestamp - start_timestamp, 6)
    print(f"PREPROCESS: FINISHED (took {time_taken} seconds)")


def run_pcxs(session: custom_types.ProffastSession) -> None:
    prf_dir = os.path.join(session.ctn.container_path, "prf")
    start_timestamp = datetime.datetime.utcnow().timestamp()
    print("PCXS10: STARTING")

    # running pcxs10
    stdout = tum_esm_utils.shell.run_shell_command(
        "./pcxs10 " + os.path.join(prf_dir, "inp_fast", "pcxs10.inp"),
        working_directory=prf_dir,
    )
    print(f"stdout:\n{stdout}")

    # renaming output files
    date_string = session.ctx.date.strftime("%Y%m%d")
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
    print(f"PCXS10: FINISHED (took {time_taken} seconds)")


def run_invers(session: custom_types.ProffastSession) -> None:
    prf_dir = os.path.join(session.ctn.container_path, "prf")
    start_timestamp = datetime.datetime.utcnow().timestamp()
    print("INVERS10: STARTING")

    # running invers10
    stdout = tum_esm_utils.shell.run_shell_command(
        'printf "Y\n%.0s" {1..100} | ./invers10 '
        + os.path.join(prf_dir, "inp_fast", "invers10.inp"),
        working_directory=prf_dir,
    )
    print(f"stdout:\n{stdout}")

    # renaming output files
    date_string = session.ctx.date.strftime("%Y%m%d")
    for f in os.listdir(f"{prf_dir}/out_fast"):
        if date_string not in f:
            os.rename(
                f"{prf_dir}/out_fast/{f}",
                f"{prf_dir}/out_fast/{f.replace(date_string[:6], date_string)}",
            )

    end_timestamp = datetime.datetime.utcnow().timestamp()
    time_taken = round(end_timestamp - start_timestamp, 6)
    print(f"INVERS10: FINISHED (took {time_taken} seconds)")
