import functools
import pandas as pd
from psycopg import sql
import scipy
import matplotlib
from src import utils
from src.custom_types import Config, RequestConfig, Date, SensorId, Campaign, Rate


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
    UTC, gnd_p, gnd_t, app_sza, azimuth, xh2o, xair, xco2, xch4, xco, xch4_s5p
    utc, gndP, gndT, appSZA, azimuth, XH2O, XAIR, XCO2, XCH4, XCO, XCH4_S5P
    """
    df = sensor_dataframe.rename(columns={
        'UTC': 'utc',
        ' gndP': 'gnd_p',
        ' gndT': 'gnd_t',
        ' appSZA': 'app_sza',
        ' XH2O': 'xh2o',
        ' XAIR': 'xair',
        ' XCO2': 'xco2',
        ' XCH4': 'xch4',
        ' XCO': 'xco',
        ' XCH4_S5P': 'xch4_s5p'
    }, errors="raise")
    sensor_dataframe = df.filter(items=['utc', 'gnd_p', 'gnd_t', 'app_sza', 'azimuth', 'xh2o', 'xair', 'xco2', 'xch4', 'xco', 'xch4_s5p'])
    sensor_dataframe.plot(x='utc', y='xco2')
    print(sensor_dataframe)
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

    ✗ sampling_rate is (as of now) a custom type Rate:Literal[
        "10 min", "5 min", "2 min", "1 min", "30 sec", "15 sec", "10 sec", "5 sec", "2 sec", "1 sec"
        ]
    
    ✗ get_daily_dataframe (see below) will be called afterwards and joins the dataframes on "utc".
    """ 
    sensor_dataframe.sort_values(by=['utc']) # sort according to time
    # Apply smoothing function for all data columns.
    for column in sensor_dataframe.columns[1::]:
        sensor_dataframe[column] = scipy.signal.savgol_filter(pd.to_numeric(sensor_dataframe[column]), 31, 3)

    sensor_dataframe = sensor_dataframe.set_index('utc')
    sensor_dataframe.index = pd.to_datetime(sensor_dataframe.index)
    df_series = sensor_dataframe.squeeze()
    output_data = df_series.resample(sampling_rate).mean()
    output_data.reset_index().plot(x='utc', y='xco2')
    #output_data.plot(x='utc', y='xco2')
    return output_data


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
