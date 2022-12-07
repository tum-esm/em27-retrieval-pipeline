from typing import Any

import psycopg

from src import custom_types


def query_pg_database(
    database_config: custom_types.DatabaseConfiguration, sql_query: str
) -> list[Any]:
    """_summary_"""

    with psycopg.connect(
        f"host={database_config.host} "
        + f"port={database_config.port} "
        + f"user={database_config.username} "
        + f"password={database_config.password} "
        + f"dbname={database_config.database_name} "
        + f"connect_timeout=10",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_query)
            return cur.fetchall()
