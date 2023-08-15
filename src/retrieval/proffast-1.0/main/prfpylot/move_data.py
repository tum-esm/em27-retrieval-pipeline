import glob
import os
import tempfile
import polars as pl
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


def _read_invparms_file(path: str) -> pl.DataFrame:
    # this tempfile is necessary because the `invparms.dat` are
    # have to be adjusted in order to be read by polars
    with tempfile.TemporaryDirectory() as d:
        with open(path, "r") as f:
            file_content = f.read()

        while "\t" in file_content:
            file_content = file_content.replace("\t", " ")

        while "  " in file_content:
            file_content = file_content.replace("  ", " ")

        with open(os.path.join(d, os.path.basename(path)), "w") as f:
            f.write(file_content)

        return pl.read_csv(
            os.path.join(d, os.path.basename(path)),
            has_header=True,
            separator=" ",
            columns=[
                "JulianDate",
                "HHMMSS_ID",
                "SX",
                "gndP",
                "gndT",
                "latdeg",
                "londeg",
                "altim",
                "appSZA",
                "azimuth",
                "XH2O",
                "XAIR",
                "XCO2",
                "XCH4",
                "XCH4_S5P",
                "XCO",
            ],
            dtypes={
                "JulianDate": pl.Float64,
                "HHMMSS_ID": str,  # type: ignore
                "SX": str,  # type: ignore
                "gndP": pl.Float64,
                "gndT": pl.Float64,
                "latdeg": pl.Float64,
                "londeg": pl.Float64,
                "altim": pl.Float64,
                "appSZA": pl.Float64,
                "azimuth": pl.Float64,
                "XH2O": pl.Float64,
                "XAIR": pl.Float64,
                "XCO2": pl.Float64,
                "XCH4": pl.Float64,
                "XCH4_S5P": pl.Float64,
                "XCO": pl.Float64,
            },
        )


def merge_output_files(session: custom_types.ProffastSession) -> None:
    out_dir = os.path.join(session.ctn.container_path, "prf", "out_fast")
    date_string = session.ctx.from_datetime.strftime("%Y%m%d")
    output_table_name = f"{session.ctx.sensor_id}{date_string[2:]}-combined-invparms"

    # merge output tables
    output_filenames = glob.glob(os.path.join(out_dir, "*invparms.dat"))
    if len(output_filenames) == 0:
        return
    merged_df = pl.concat(
        [_read_invparms_file(f) for f in output_filenames],
        how="vertical",
    )

    # export as csv (quick inspection) and parquet (further processing)
    merged_df.write_csv(
        os.path.join(out_dir, f"{output_table_name}.csv"),
        separator=",",
        has_header=True,
    )
    merged_df.write_parquet(
        os.path.join(out_dir, f"{output_table_name}.parquet"),
    )
