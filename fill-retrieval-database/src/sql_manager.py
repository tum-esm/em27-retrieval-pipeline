from pandas import DataFrame
from sqlalchemy import create_engine, MetaData, Table, and_, or_
from sqlalchemy_utils import database_exists, create_database

from src.config import Config


class SqlManager:
    def __init__(self, properties: Config):
        self.properties = properties
        self.__create_engine()

    def __create_engine(self):
        properties = self.properties
        self.engine = create_engine(
            "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
                properties.db_username,
                properties.db_password,
                properties.db_ip,
                properties.db_port,
                properties.database_name,
            )
        )

    def insert_from_df(self, new_rows: DataFrame):
        if not new_rows.empty:
            print("Found new rows(#{}), writing to db".format(len(new_rows.index)))
            new_rows.to_sql(
                "measurements",
                self.engine,
                schema="public",
                if_exists="append",
                index=False,
                index_label=None,
                chunksize=None,
                dtype=None,
                method=None,
            )

    def update_dataframe(self, modified_rows: DataFrame):
        if not modified_rows.empty:
            print("Found modified rows(#{}), updating".format(len(modified_rows.index)))
            modified_rows.to_sql(
                "measurements",
                self.engine,
                schema="public",
                if_exists="replace",
                index=False,
                index_label=None,
                chunksize=None,
                dtype=None,
                method=None,
            )

    def delete_rows(self, removed_rows: DataFrame):
        if not removed_rows.empty:
            print(
                "Found deleted rows(#{}), deleting them from the database either".format(
                    len(removed_rows.index)
                )
            )

            meta = MetaData()

            measurements_table = Table(
                "measurements", meta, autoload=True, autoload_with=self.engine
            )

            cond = removed_rows.apply(
                lambda row: and_(
                    measurements_table.c["utc"] == row["utc"],
                    measurements_table.c["sensor"] == row["sensor"],
                    measurements_table.c["retrieval_software"]
                    == row["retrieval_software"],
                ),
                axis=1,
            )
            cond = or_(*cond)

            delete = measurements_table.delete().where(cond)
            with self.engine.connect() as conn:
                conn.execute(delete)

    def init_db(self):
        if not database_exists(self.engine.url):
            create_database(self.engine.url)

        with open("scripts/init_db.sql", "r") as sql_file:
            self.engine.execute(sql_file.read())
        return
