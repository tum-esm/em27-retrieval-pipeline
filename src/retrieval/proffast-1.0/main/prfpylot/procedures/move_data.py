import os
from src import custom_types


def move_bin_files(session: custom_types.ProffastSession) -> None:
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    src_dir = os.path.join(session.ctn.data_input_path, "ifg", date_string[2:], "cal")
    dst_dir = os.path.join(
        session.ctn.data_output_path,
        "analysis",
        session.ctx.sensor_id,
        date_string[2:],
        "cal",
    )
    assert not os.path.exists(dst_dir)
    os.rename(src_dir, dst_dir)


def merge_output_files(session: custom_types.ProffastSession) -> None:
    raise NotImplementedError()
