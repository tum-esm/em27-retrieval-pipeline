import glob
import os

import pandas
from pandas import DataFrame
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

from config import Config

dictionary_columns = {
    'UTC': 'utc',
    'gndP': 'gnd_p',
    'gndT': 'gnd_t',
    'appSZA': 'app_sza',
    'azimuth': 'azimuth',
    'XH2O': 'xh2o',
    'XAIR': 'xair',
    'XCO2': 'xco2',
    'XCH4': 'xch4',
    'XCO': 'xco',
    'XCH4_S5P': 'xch4_s5p',
    'H2O': 'h2o',
    'O2': 'o2',
    'CO2': 'co2',
    'CH4': 'ch4',
    'CO': 'co',
    'CH4_S5P': 'ch4_s5p',
    'sensor': 'sensor',
    'retrieval_software': 'retrieval_software'
}


def build_data_frame_from(filepath, version):
    df = pandas.read_csv(filepath, header=0)
    df.rename(columns=lambda x: x.strip(), inplace=True)

    df.drop('LocalTime', axis=1, inplace=True)
    df.drop('spectrum', axis=1, inplace=True)
    df.drop('JulianDate', axis=1, inplace=True)
    df.drop('UTtimeh', axis=1, inplace=True)
    df.drop('latdeg', axis=1, inplace=True)
    df.drop('londeg', axis=1, inplace=True)
    df.drop('altim', axis=1, inplace=True)

    df['sensor'] = get_sensor_type(filepath)
    df['retrieval_software'] = version

    df.rename(columns=lambda x: rename_columns(x), inplace=True)

    return df


def get_sensor_type(filepath):
    for s in ["ma", "mb", "mc", "md", "me"]:
        if filepath.endswith(f'{s}.csv'):
            return s


def rename_columns(column):
    return dictionary_columns[column]


def process_csv(properties):
    cached_data_frame = DataFrame(columns=list(dictionary_columns.values()))

    if os.path.isfile(properties.cache_file_location):
        cached_data_frame = pandas.read_hdf(properties.cache_file_location)
        print('Cache found.')
        print(cached_data_frame)

    for location in properties.csv_locations:
        print('Started reading CSVs from a new location')
        # path = '../{}/comb_invparms_*_SN???_??????-??????.csv'.format(location)
        path = '{}/proffast-?.?-outputs-????????-??.csv'.format(location)

        files = glob.glob(path)

        dfs = list()

        engine = create_engine(
            'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(properties.db_username, properties.db_password,
                                                          properties.db_ip,
                                                          properties.db_port, properties.database_name))

        for f in files:
            df = build_data_frame_from(f, settings.retrieval_version)

            dfs.append(df)

        if not dfs:
            print('Nothing found.')
            continue

        print('Done reading CSVs, started to analyze data.')

        df = pandas.concat(dfs, ignore_index=True)

        new_rows = pandas.merge(df, cached_data_frame, indicator=True, how='left',
                                on=['utc', 'sensor', 'retrieval_software'], suffixes=('', '_y')) \
            .query('_merge=="left_only"') \
            .drop('_merge', axis=1)

        new_rows.drop(new_rows.filter(regex='_y$').columns, axis=1, inplace=True)

        if not new_rows.empty:
            print('Found new rows, writing to db')
            new_rows.to_sql(
                'measurements',
                engine,
                schema='public',
                if_exists='append',
                index=False,
                index_label=None,
                chunksize=None,
                dtype=None,
                method=None
            )

        modified_rows = pandas.merge(df, cached_data_frame, indicator=True, how='left', suffixes=('', '_y')) \
            .query('_merge=="left_only"') \
            .drop('_merge', axis=1)

        modified_rows.drop(modified_rows.filter(regex='_y$').columns, axis=1, inplace=True)

        modified_rows = modified_rows[~modified_rows.index.isin(new_rows.index)]

        if not modified_rows.empty:
            print('Found modified rows, updating')
            modified_rows.to_sql(
                'measurements',
                engine,
                schema='public',
                if_exists='replace',
                index=False,
                index_label=None,
                chunksize=None,
                dtype=None,
                method=None
            )

        print('Refreshing cache.')

        df.to_hdf(properties.cache_file_location, key='df', mode='a')

        print('Done refreshing cache.')


def init_db(properties):
    engine = create_engine(
        'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(properties.db_username, properties.db_password, properties.db_ip,
                                                      properties.db_port, properties.database_name))
    if not database_exists(engine.url):
        create_database(engine.url)

    with open('scripts/init_db.sql', 'r') as sql_file:
        engine.execute(sql_file.read())


if __name__ == '__main__':

    settings = Config('./config/config.properties')

    option = input('Do you want to create a database(1) or process csv files(2)?\n')
    if option == '1':
        init_db(settings)
    elif option == '2':
        process_csv(settings)
