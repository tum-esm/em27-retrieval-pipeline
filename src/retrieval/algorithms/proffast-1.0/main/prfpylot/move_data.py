import glob
import os
from src import utils, retrieval


def move_bin_files(session: utils.types.RetrievalSession) -> None:
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    src_dir = os.path.join(
        session.ctn.data_input_path, "ifg", date_string[2 :], "cal"
    )
    dst_dir = os.path.join(
        session.ctn.data_output_path,
        "analysis",
        session.ctx.sensor_id,
        date_string[2 :],
        "cal",
    )
    assert not os.path.exists(dst_dir)
    os.rename(src_dir, dst_dir)


def merge_output_files(session: utils.types.RetrievalSession) -> None:
    out_dir = os.path.join(session.ctn.container_path, "prf", "out_fast")
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    output_table_name = f"{session.ctx.sensor_id}{date_string[2:]}-combined-invparms"

    # merge output tables
    output_filenames = glob.glob(os.path.join(out_dir, "*invparms.dat"))
    merged_df = retrieval.utils.invparms_files.read_and_merge_invparms_files(
        output_filenames
    )
    if merged_df is None:
        return

    # export as csv (quick inspection) and parquet (further processing)
    merged_df.write_csv(
        os.path.join(out_dir, f"{output_table_name}.csv"),
        separator=",",
        has_header=True,
    )
    merged_df.write_parquet(
        os.path.join(out_dir, f"{output_table_name}.parquet"),
    )
