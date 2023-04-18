import functools
import os
from typing import Literal
import numpy as np
from scipy.signal import savgol_filter
import polars as pl
import tum_esm_em27_metadata
from src import custom_types


def get_empty_sensor_dataframe(
    sensor_id: str,
    output_merging_target: custom_types.config.OutputMergingTargetConfig,
) -> pl.DataFrame:
    """
    Returns an empty single sensor dataframe.

    The dataframe contains raw station data for one day and one sensor.
    Each requested data type is parsed into a column. The column names
    are prefixed with the sensor id. Example:

    ```
    utc  me_gnd_p  me_gnd_t  me_app_sza  ...
    ```
    """

    column_names = [
        f"{sensor_id}_{type_}" for type_ in output_merging_target.data_types
    ]

    return pl.DataFrame(
        schema={
            "utc": pl.Datetime,
            **{c: pl.Float32 for c in column_names},
        }
    )


def get_sensor_dataframe(
    config: custom_types.Config,
    sensor_data_context: tum_esm_em27_metadata.types.SensorDataContext,
    output_merging_target: custom_types.config.OutputMergingTargetConfig,
) -> pl.DataFrame:
    """
    Returns a single sensor dataframe.

    The dataframe contains raw station data for one day and one sensor.
    Each requested data type is parsed into a column. The column names
    are prefixed with the sensor id. Example:

    ```
    utc                     me_gnd_p  me_gnd_t  me_app_sza  ...
    2021-10-20 07:00:23     950.91    289.05    78.45       ...
    2021-10-20 07:00:38     950.91    289.05    78.42       ...
    2021-10-20 07:01:24     950.91    289.05    78.31       ...
    ...                       ...       ...      ...
    [1204 rows x 8 columns]
    ```
    """

    raw_csv_path = os.path.join(
        config.general.data_dst_dirs.results,
        sensor_data_context.sensor_id,
        "proffast-2.2-outputs/successful",
        sensor_data_context.date,
        f"comb_invparms_{sensor_data_context.sensor_id}_"
        + f"SN{str(sensor_data_context.serial_number).zfill(3)}_"
        + f"{sensor_data_context.date[2:]}-{sensor_data_context.date[2:]}.csv",
    )
    assert os.path.isfile(raw_csv_path), f"file {raw_csv_path} does not exist."

    all_data_types = [
        "gnd_p",
        "gnd_t",
        "app_sza",
        "azimuth",
        "xh2o",
        "xair",
        "xco2",
        "xch4",
        "xco",
        "xch4_s5p",
    ]

    df = pl.read_csv(
        raw_csv_path,
        columns=[
            "UTC",
            " gndP",
            " gndT",
            " appSZA",
            " azimuth",
            " XH2O",
            " XAIR",
            " XCO2",
            " XCH4",
            " XCO",
            " XCH4_S5P",
        ],
        new_columns=[
            "utc",
            *[f"{sensor_data_context.sensor_id}_{t}" for t in all_data_types],
        ],
        dtypes={
            "utc": pl.Datetime,
            **{
                f"{sensor_data_context.sensor_id}_{t}": pl.Float32
                for t in all_data_types
            },
        },
    )

    # only keep the requested columns
    return df.select(
        [
            "utc",
            *[
                f"{sensor_data_context.sensor_id}_{type_}"
                for type_ in output_merging_target.data_types
            ],
        ]
    )


def post_process_dataframe(
    df: pl.DataFrame,
    sampling_rate: Literal[
        "10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s", "1s"
    ],
    max_interpolation_gap_seconds: int,
) -> pl.DataFrame:
    """Post-processes the dataframe.

    It will resample the data to the required sampling rate using the savgol_filter. It will interpolate missing values up to the MAX_DELTA_FOR_INTERPOLATION timespan.

    `df` is the output of get_sensor_dataframe (see above). Example:

    ```
                            me_gnd_p  me_gnd_t  me_app_sza  ...
    utc
    2021-10-20 07:00:23     950.91    289.05       78.45     ...
    2021-10-20 07:00:38     950.91    289.05       78.42     ...
    2021-10-20 07:01:24     950.91    289.05       78.31     ...
    ...                       ...       ...         ...
    [1204 rows x 8 columns]
    ```

    ✗ `get_daily_dataframe` (see below) will be called afterwards and joins the dataframes on "utc".
    """

    if len(df) < 31:
        return df

    # add rows with only nan values in gaps larger than the
    # MAX_DELTA_FOR_INTERPOLATION timespan. This is necessary
    # because the savgol_filter does not consider gap size but
    # only the size of the window. I.e. a data point that is
    # 2 hours away from the current data point should not
    # influence the smoothed value of the current data point
    # even if that point is the next point.

    lower_utc_bound: pl.Datetime = (
        df.select(pl.min("utc") - pl.duration(seconds=1)).to_series().to_list()[0]
    )
    upper_utc_bound: pl.Datetime = (
        df.select(pl.max("utc") + pl.duration(seconds=1)).to_series().to_list()[0]
    )
    utcs_in_gaps: list[pl.Datetime] = (
        df.select(pl.col("utc"))
        .with_columns(pl.col("utc").diff().alias("dutc"))
        .filter(pl.col("dutc") > pl.duration(seconds=max_interpolation_gap_seconds))
        .select(pl.col("utc") - pl.duration(seconds=1))
        .to_series()
        .to_list()
    )
    new_utc_rows = [lower_utc_bound] + utcs_in_gaps + [upper_utc_bound]

    new_df = pl.DataFrame(
        {
            "utc": new_utc_rows,
            **{
                column_name: [np.nan] * len(new_utc_rows)
                for column_name in df.columns
                if column_name != "utc"
            },
        },
        schema={
            "utc": pl.Datetime,
            **{
                column_name: pl.Float32
                for column_name in df.columns
                if column_name != "utc"
            },
        },
    )

    df = pl.concat([df, new_df]).sort("utc")

    # apply savgol_filter on the data columns
    df = df.select(
        pl.col("utc"),
        pl.exclude("utc")
        .map(lambda x: savgol_filter(x.to_numpy(), 31, 3).tolist())
        .arr.explode(),
    )

    # Upscale to 1s intervals and interpolate when the gaps
    # are smaller than the MAX_DELTA_FOR_INTERPOLATION. Finally,
    # downsample to the required sampling rate with a mean
    # aggregation on the data columns.
    df = (
        df.with_columns(
            (
                pl.col("utc") - pl.col("utc").shift()
                < pl.duration(seconds=max_interpolation_gap_seconds)
            ).alias("small_gap")
        )
        .upsample(time_column="utc", every="1s")
        .with_columns(pl.col("small_gap").backward_fill())
        .with_columns(
            pl.when(pl.col("small_gap"))
            .then(pl.exclude(["small_gap"]).interpolate())
            .otherwise(pl.exclude(["small_gap"]))
        )
        .select(pl.exclude("small_gap"))
        .groupby_dynamic("utc", every=sampling_rate)
        .agg(pl.exclude("utc").mean())
    )

    return df


def merge_dataframes(
    dfs: list[pl.DataFrame],
) -> pl.DataFrame:
    """Merges the dataframes into a single dataframe by
    joining them on the "utc" column."""

    return (
        functools.reduce(
            lambda a, b: a.join(b, how="outer", left_on="utc", right_on="utc"),
            dfs,
        )
        .filter(~pl.all(pl.all().is_null()))
        .sort("utc")
    )
