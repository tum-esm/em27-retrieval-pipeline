import pandas

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


def rename_columns(column):
    return dictionary_columns[column]


def get_sensor_type(filepath):
    for s in ["ma", "mb", "mc", "md", "me"]:
        if filepath.endswith(f'{s}.csv'):
            return s


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


def detect_new(df_from_csv, df_from_cache):
    new_rows = pandas.merge(df_from_csv, df_from_cache, indicator=True, how='left',
                            on=['utc', 'sensor', 'retrieval_software'], suffixes=('', '_y')) \
        .query('_merge=="left_only"') \
        .drop('_merge', axis=1)

    new_rows.drop(new_rows.filter(regex='_y$').columns, axis=1, inplace=True)
    return new_rows


def detect_modified(df_from_csv, df_from_cache, new_rows):
    modified_rows = pandas.merge(df_from_csv, df_from_cache, indicator=True, how='left', suffixes=('', '_y')) \
        .query('_merge=="left_only"') \
        .drop('_merge', axis=1)

    modified_rows.drop(modified_rows.filter(regex='_y$').columns, axis=1, inplace=True)

    modified_rows = modified_rows[~modified_rows.index.isin(new_rows.index)]

    return modified_rows


def detect_deleted(df_from_csv, df_from_cache):
    removed_rows = pandas.merge(df_from_csv, df_from_cache, indicator=True, how='right',
                                on=['utc', 'sensor', 'retrieval_software'], suffixes=('_y', '')) \
        .query('_merge=="right_only"') \
        .drop('_merge', axis=1)

    removed_rows.drop(removed_rows.filter(regex='_y$').columns, axis=1, inplace=True)
    return removed_rows


def detect_all_years_in_dataframe(df):
    df['year'] = pandas.DatetimeIndex(df['utc']).year
    return df['year'].unique()


def filter_dataframe(df, year):
    return df.loc[(pandas.DatetimeIndex(df['utc']).year == year)]
