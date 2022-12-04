import datetime
import psycopg
import pandas as pd
from typing import Any
from src import custom_types


def _run_database_request(
    database_config: custom_types.DatabaseConfig, sql_query_string: str
) -> list[Any]:
    """run a single SQL "SELECT" query"""
    with psycopg.connect(
        f"host={database_config.host} "
        + f"port={database_config.port} "
        + f"user={database_config.username} "
        + f"password={database_config.password} "
        + f"dbname={database_config.database_name} "
        + f"connect_timeout=10",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_query_string)
            return cur.fetchall()


def _get_raw_station_data(
    database_config: custom_types.DatabaseConfig,
    proffast_version: str,
    station_id: custom_types.StationId,
    date_string: custom_types.Date,
) -> pd.DataFrame:
    """
    Get a pd.DataFrame for a single station id and a single date.
    The returned table will have one row every exact minute where
    data exists.

    returned column names: utc, gnd_p, gnd_t, app_sza, xh2o, xair,
    xco2, xch4, xco (all columns except for utc are prefixed with
    the station id, e.g. "ma_...")

    output example:

    ```
                           ma_gnd_p  ma_gnd_t  ma_app_sza
    utc_time
    2021-01-09 10:18:00  956.156667    269.62   71.510000  ...
    2021-01-09 10:19:00  956.143333    269.62   71.480000  ...
    2021-01-09 10:20:00  956.137500    269.62   71.435000  ...
    ...                         ...       ...         ...  ...

    [221 rows x 8 columns]
    ```
    """
    from_date = datetime.datetime.strptime(date_string, "%Y%m%d")
    to_date = from_date + datetime.timedelta(days=1)

    results = _run_database_request(
        database_config,
        f"""
            SELECT
                utc, gnd_p, gnd_t, app_sza,
                xh2o, xair, xco2, xch4, xco
            FROM measurements
            WHERE
                retrieval_software = '{proffast_version}' AND
                sensor = '{station_id}' AND
                utc >= '{from_date.strftime("%Y-%m-%d")}' AND
                utc < '{to_date.strftime("%Y-%m-%d")}'
        """,
    )

    df = (
        pd.DataFrame(
            results,
            columns=[
                "utc_time",
                f"{station_id}_gnd_p",
                f"{station_id}_gnd_t",
                f"{station_id}_app_sza",
                f"{station_id}_xh2o",
                f"{station_id}_xair",
                f"{station_id}_xco2",
                f"{station_id}_xch4",
                f"{station_id}_xco",
            ],
        )
        .set_index("utc_time")
        .astype(float)
    )

    return df.groupby(pd.Grouper(freq="1min")).mean()


def get_daily_dataframe(
    database_config: custom_types.DatabaseConfig,
    proffast_version: str,
    station_ids: list[custom_types.StationId],
    date_string: custom_types.Date,
) -> pd.DataFrame:
    """
    Get a pd.DataFrame for a list of station ids and a single date.
    The returned table will have one row every exact minute where
    data exists. Rows can contain "NaN" values, when not all stations
    sent anything in that minute.

    returned column names (all columns for each station id): utc, gnd_p,
    gnd_t, app_sza, xh2o, xair, xco2, xch4, xco (all columns except for
    utc are prefixed with their station id, e.g. "ma_...")

    output example:

    ```
                           ma_gnd_p  ma_gnd_t  ma_app_sza
    utc_time
    2021-01-09 10:18:00  956.156667    269.62   71.510000  ...
    2021-01-09 10:19:00  956.143333    269.62   71.480000  ...
    2021-01-09 10:20:00  956.137500    269.62   71.435000  ...
    ...                         ...       ...         ...  ...

    [221 rows x 8 columns]
    ```
    """

    merged_df = None
    for station_id in station_ids:
        df = _get_raw_station_data(
            database_config, proffast_version, station_id, date_string
        )
        if merged_df is None:
            merged_df = df
        else:
            merged_df = merged_df.join(df, how="outer")

    return merged_df.dropna(axis=0, how="all").fillna("NaN")
