import functools
import os
from typing import Literal
from scipy.signal import savgol_filter
import polars as pl
import tum_esm_em27_metadata
from src import custom_types


# Hardcoding max delta for interpolation. Gaps
# greater than this are not interpolated.
MAX_DELTA_FOR_INTERPOLATION = pl.duration(minutes=3)


def get_sensor_dataframe(
    config: custom_types.Config,
    output_merging_target: custom_types.config.OutputMergingTargetConfig,
    date_string: str,
    sensor: tum_esm_em27_metadata.types.Sensor,
) -> pl.DataFrame:
    """
    Returns a single sensor dataframe.

    The dataframe contains raw station data for one day and one sensor.
    Each requested data type is parsed into a column. The column names
    are prefixed with the sensor id. Example:

                            me_gnd_p  me_gnd_t  me_app_sza  ...
    utc
    2021-10-20 07:00:23     950.91    289.05       78.45     ...
    2021-10-20 07:00:38     950.91    289.05       78.42     ...
    2021-10-20 07:01:24     950.91    289.05       78.31     ...
    ...                       ...       ...         ...
    [1204 rows x 8 columns]
    """

    raw_csv_path = os.path.join(
        config.general.data_dst_dirs.results,
        sensor.sensor_id,
        "proffast-2.2-outputs/successful",
        date_string,
        f"comb_invparms_ma_SN{str(sensor.serial_number).zfill(3)}_"
        + f"{date_string[2:]}-{date_string[2:]}.csv",
    )
    column_names = [f"{sensor}_{type_}" for type_ in output_merging_target.data_types]

    if not os.path.isfile(raw_csv_path):
        return pl.DataFrame(
            schema={"utc": pl.Datetime, **{c: pl.Float64 for c in column_names}}
        )

    return pl.read_csv(
        raw_csv_path,
        new_columns=[
            "utc",
            "XX_LocalTime",
            "XX_spectrum",
            "XX_JulianDate",
            "XX_UTtimeh",
            f"{sensor.sensor_id}_gnd_p",
            f"{sensor.sensor_id}_gnd_t",
            "XX_latdeg",
            "XX_londeg",
            "XX_altim",
            f"{sensor.sensor_id}_app_sza",
            f"{sensor.sensor_id}_azimuth",
            f"{sensor.sensor_id}_xh2o",
            f"{sensor.sensor_id}_xair",
            f"{sensor.sensor_id}_xco2",
            f"{sensor.sensor_id}_xch4",
            f"{sensor.sensor_id}_xco",
            f"{sensor.sensor_id}_xch4_s5p",
            "XX_H2O",
            "XX_O2",
            "XX_CO2",
            "XX_CH4",
            "XX_CO",
            "XX_CH4_S5P",
        ],
        columns=["utc", *column_names],
        dtypes={"utc": pl.Datetime, **{c: pl.Float64 for c in column_names}},
    )


def post_process_dataframe(
    df: pl.DataFrame,
    sampling_rate: Literal[
        "10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s", "1s"
    ],
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

    # Convert utc to datetime and apply savgol_filter on the data columns
    q = df.lazy().select(
        [
            pl.col("utc"),
            pl.exclude("utc")
            .map(lambda x: savgol_filter(x.to_numpy(), 31, 3))
            .arr.explode(),
        ]
    )
    df = q.collect()

    # Upscale to 1s intervals and interpolate when the gaps are smaller than the MAX_DELTA_FOR_INTERPOLATION
    # Finally, downsample to the required sampling rate with a mean aggregation on the data columns.
    df = (
        df.with_columns(
            (pl.col("utc") - pl.col("utc").shift() < MAX_DELTA_FOR_INTERPOLATION).alias(
                "small_gap"
            )
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
            lambda a, b: a.join(
                b, how="outer", left_on="utc", right_on="utc", suffix=""
            ),
            dfs,
        )
        .drop_nulls()
        .sort("utc")
    )
