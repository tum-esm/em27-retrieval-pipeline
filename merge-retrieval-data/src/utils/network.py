import psycopg
import requests
from typing import Any
from src.custom_types import DatabaseConfig


def request_url(
    url: str,
    username: str,
    password: str,
    timeout: int = 10,
) -> str:
    """Sends a request and returns the content of the response, in unicode."""
    response = requests.get(url, auth=(username, password), timeout=timeout)
    response.raise_for_status()
    return response.text


def query_pg_database(
    config: DatabaseConfig, query: psycopg.sql.Composed, params: dict[str, Any]
) -> list[tuple[Any, ...]]:
    """
    Queries PostgreSQL database and returns all records. Parameters are
    passed separately and will be merged to the query (server-side binding).
    """
    with psycopg.connect(
        f"host={config.host} "
        + f"port={config.port} "
        + f"user={config.username} "
        + f"password={config.password} "
        + f"dbname={config.database_name} "
        + f"connect_timeout=10",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
