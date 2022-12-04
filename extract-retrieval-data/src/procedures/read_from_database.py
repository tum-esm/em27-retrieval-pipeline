import datetime
import psycopg
from typing import Any
from src import custom_types


def _run_database_request(
    database_config: custom_types.DatabaseConfig, sql_query_string: str
) -> list[Any]:
    with psycopg.connect(
        " ".join(
            [
                f"host={database_config.host}",
                f"port={database_config.port}",
                f"user={database_config.username}",
                f"password={database_config.password}",
                f"dbname={database_config.database_name}",
                f"connect_timeout=10",
            ]
        )
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_query_string)
            results = cur.fetchall()

    return results


def get_raw_station_data(
    database_config: custom_types.DatabaseConfig,
    proffast_version: str,
    station_id: custom_types.StationId,
    date_string: custom_types.Date,
) -> None:
    from_date = datetime.datetime.strptime(date_string, "%Y%m%d")
    to_date = from_date + datetime.timedelta(days=1)

    results = _run_database_request(
        database_config,
        f"""
    SELECT
        utc,
        gnd_p, gnd_t, app_sza,
        xh2o, xair, xco2, xch4, xco
    FROM measurements
    WHERE
        retrieval_software = '{proffast_version}' AND
        sensor = '{station_id}' AND
        utc >= '{from_date.strftime("%Y-%m-%d")}' AND
        utc < '{to_date.strftime("%Y-%m-%d")}'
    """,
    )

    print(results)
