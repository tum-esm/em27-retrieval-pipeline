import glob

import pandas
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

from config import Config


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
    dictionary = {
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

    return dictionary[column]


def process_csv(properties):
    for location in properties.csv_locations:
        # path = '../{}/comb_invparms_*_SN???_??????-??????.csv'.format(location)
        path = '../{}/proffast-?.?-outputs-????????-??.csv'.format(location)

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
            continue

        df = pandas.concat(dfs, ignore_index=True)

        print(df)

        df.to_sql(
            'measurements',
            engine,
            schema='public',
            if_exists='append',
            index=False,
            index_label=None,
            chunksize=None,
            dtype=None,
            method=None,
        )


def init_db(properties):
    engine = create_engine(
        'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(properties.db_username, properties.db_password, properties.db_ip,
                                                      properties.db_port, properties.database_name))
    if not database_exists(engine.url):
        create_database(engine.url)

    with open('../scripts/init_db.sql', 'r') as sql_file:
        engine.execute(sql_file.read())


if __name__ == '__main__':

    settings = Config('../config/config.properties')

    option = input('Do you want to create a database(1) or process csv files(2)?\n')
    if option == '1':
        init_db(settings)
    elif option == '2':
        process_csv(settings)
