from typing import Optional
import tempfile
import polars as pl
import os


def read_and_merge_invparms_files(paths: list[str]) -> Optional[pl.DataFrame]:
    dfs: list[pl.DataFrame] = []

    for path in paths:
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

            dfs.append(
                pl.read_csv(
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
                    schema_overrides={
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
            )

    if len(dfs) == 0:
        return None

    return pl.concat(dfs, how="vertical")
