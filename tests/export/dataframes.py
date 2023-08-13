import datetime
import polars as pl
from src import procedures


def _is_subset(df1: pl.DataFrame, df2: pl.DataFrame) -> bool:
    """Check whether all cells of `df1` are included in `df2`."""

    for utc in df1.get_column("utc"):
        for col in df1.columns:
            if col == "utc":
                continue
            df1_val = df1.filter(pl.col("utc") == utc).get_column(col)[0]
            if df1_val in [None, pl.Null]:
                continue
            try:
                df2_val = df2.filter(pl.col("utc") == utc).get_column(col)[0]
                assert df1_val == df2_val
            except (pl.ColumnNotFoundError, AssertionError, pl.ComputeError):
                print(f'column "{col}" at utc "{utc}" not correct in df2')
                return False

    return True


def test_merge_dataframes() -> None:
    get_t = lambda minute: datetime.datetime(2021, 1, 1, 0, minute, 0)

    df1 = pl.DataFrame({"utc": [get_t(1), get_t(2), get_t(3)], "b": [1, 2, None]})
    df2 = pl.DataFrame({"utc": [get_t(4), get_t(5), get_t(6)], "b": [4, 5, 6]})
    df3 = pl.DataFrame({"utc": [get_t(2), get_t(3), get_t(4)], "c": [7, None, 9]})

    df4 = procedures.export.merge_dataframes([df1, df2, df3])
    print(df4)

    assert _is_subset(df1, df4)
    assert _is_subset(df2, df4)
    assert _is_subset(df3, df4)
