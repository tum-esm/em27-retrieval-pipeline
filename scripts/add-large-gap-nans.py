import numpy as np
import polars as pl
from scipy.signal import savgol_filter

MAX_GAP_DIFF = 10

raw_df = pl.DataFrame(
    {
        "t": [1, 2, 3, 20, 21, 22],
        "a": [1, 2, 3, 4, 5, 6],
    },
    schema={
        "t": pl.Int64,
        "a": pl.Float64,
    },
)

ts = raw_df.select(pl.col("t")).to_series().to_list()
ts_in_gaps: list[int] = (
    raw_df.with_columns(pl.col("t").diff().alias("dt"))
    .filter(pl.col("dt") > MAX_GAP_DIFF)
    .select(pl.col("t") - 1)
    .to_series()
    .to_list()
)

new_ts = [min(ts) - 1] + ts_in_gaps + [max(ts) + 1]

new_df = pl.DataFrame(
    {
        "t": new_ts,
        **{
            column_name: [np.nan] * len(new_ts)
            for column_name in raw_df.columns
            if column_name != "t"
        },
    },
    schema={
        "t": pl.Int64,
        "a": pl.Float64,
    },
)

merged_df = pl.concat([raw_df, new_df]).sort("t")

print(raw_df)
print(merged_df)

# a = [np.nan, 1, 2, 3, np.nan, 5, 12, 13, np.nan]
# print(a)
# print([(x if np.isnan(x) else round(x)) for x in savgol_filter(a, 3, 1).tolist()])
