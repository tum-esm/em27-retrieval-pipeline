import os
import shutil
from src import types, retrieval


def run(
    config: types.Config,
    logger: retrieval.utils.logger.Logger,
    session: types.RetrievalSession,
) -> None:
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")

    src_filepath = os.path.join(
        config.general.data.datalogger.root,
        session.ctx.pressure_data_source,
        f"datalogger-{session.ctx.pressure_data_source}-{date_string}.csv",
    )
    dst_filepath = os.path.join(
        session.ctn.data_input_path,
        "log",
        f"datalogger-{session.ctx.pressure_data_source}-{date_string}.csv",
    )

    assert os.path.isfile(src_filepath), "no datalogger file found"
    with open(src_filepath) as f:
        log_file_line_count = f.read().count("\n") + 1

    # 1440 minutes per day + 1 header line
    if log_file_line_count < 1441:
        logger.warning(
            f"{session.ctx.sensor_id}/{date_string} - " +
            f"datalogger file only has {log_file_line_count}/1441 lines"
        )
    assert log_file_line_count >= 120, "datalogger file has less than 120 entries"

    # apply pressure calibration and save file
    shutil.copyfile(src_filepath, dst_filepath)
