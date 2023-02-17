import functools
import pandas as pd
from psycopg import sql
from scipy.signal import savgol_filter
import polars as pl
from src import utils
from src.custom_types import Config, RequestConfig, Date, SensorId, Campaign, Rate


# Hardcoding max delta for interpolation. Gaps smaller than this are not interpolated.
MAX_DELTA_FOR_INTERPOLATION = pl.duration(minutes=3)


def get_sensor_dataframe(config: Config, date: Date, sensor: SensorId) -> pd.DataFrame:
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

    result = utils.network.query_pg_database(
        config.database,
        sql.SQL(
            """
            SELECT utc, {data_types} FROM {table}
            WHERE utc >= %(date)s AND utc < %(date)s + INTERVAL '1 day'
            AND retrieval_software = %(version)s
            AND sensor = %(sensor)s;
            """
        ).format(
            data_types=sql.SQL(", ").join(map(sql.Identifier, config.request.data_types)),
            table=sql.Identifier(config.database.table_name),
        ),
        {
            "date": date,
            "version": config.request.proffast_version,
            "sensor": sensor,
        },
    )
    columns = ["utc"] + [f"{sensor}_{type_}" for type_ in config.request.data_types]
    return pd.DataFrame(result, columns=columns).set_index("utc").astype(float)

def post_process_dataframe(
    sensor_dataframe: pd.DataFrame,
    sampling_rate: Rate,
) -> pd.DataFrame:
    """Post-processes the dataframe."""

    """
    ✗ sensor_dataframe is the output of get_sensor_dataframe (see above)
        Example:
                                me_gnd_p  me_gnd_t  me_app_sza  ...
        utc                                                         
        2021-10-20 07:00:23     950.91    289.05       78.45     ...
        2021-10-20 07:00:38     950.91    289.05       78.42     ...
        2021-10-20 07:01:24     950.91    289.05       78.31     ...
        ...                       ...       ...         ...      
        [1204 rows x 8 columns]

    ✗ sampling_rate is (as of now) a custom type Rate:Literal [
        "10m", "5m", "2m", "1m", "30s", "15s", "10s", "5s", "2s", "1s"
    ]
    
    ✗ get_daily_dataframe (see below) will be called afterwards and joins the dataframes on "utc".
    """
    # Convert to polars Dataframe
    df = pl.from_pandas(sensor_dataframe)

    # Convert utc to datetime and apply savgol_filter on the data columns 
    q = df.lazy().with_column(pl.col('utc').str.strptime(pl.Datetime, fmt='%F %T').cast(pl.Datetime)).select([pl.col('utc'),
                    pl.exclude('utc').map(lambda x: savgol_filter(x.to_numpy(), 31, 3)).arr.explode()])
    df = q.collect()

    # Upscale to 1s intervals and interpolate when the gaps are smaller than the MAX_DELTA_FOR_INTERPOLATION
    # Finally, downsample to the required sampling rate with a mean aggregation on the data columns.
    df = df.with_columns(
            (pl.col('utc')-pl.col('utc').shift()<MAX_DELTA_FOR_INTERPOLATION).alias('small_gap')) \
        .upsample(time_column="utc", every="1s") \
        .with_columns(pl.col('small_gap').backward_fill()) \
        .with_columns(
            pl.when(pl.col('small_gap')) \
                .then(pl.exclude(['small_gap']).interpolate()) \
                .otherwise(pl.exclude(['small_gap']))) \
        .select(pl.exclude('small_gap')).groupby_dynamic("utc", every=sampling_rate).agg(pl.exclude('utc').mean())

    output = df.to_pandas()
    return output


def get_daily_dataframe(
    config: RequestConfig, campaign: Campaign, sensor_dataframes: dict[SensorId, pd.DataFrame]
) -> pd.DataFrame:
    """
    Merges sensor dataframes on their indexes, removes fully empty rows,
    adds empty columns for missing stations and sorts the column names.
    """

    # Get missing stations
    sensors = {station.sensor for station in campaign.stations}
    missing_columns = [
        f"{missing_sensor}_{type_}"
        for missing_sensor in sensors - sensor_dataframes.keys()
        for type_ in config.data_types
    ]

    # Sorted merge and remove empty rows
    daily_dataframe = functools.reduce(
        lambda df1, df2: pd.merge(df1, df2, how="outer", left_index=True, right_index=True),
        sensor_dataframes.values(),
    ).dropna(axis=0, how="all")

    # Add missing stations and sort column names
    return daily_dataframe.reindex(
        sorted(daily_dataframe.columns.tolist() + missing_columns), axis=1
    )
