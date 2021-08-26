"""
Project Description:
This program is part of the master thesis of Nico Nachtigall. It contains all functions, which are needed in addition to
the filter and background functions.

Author: Nico Nachtigall
created: September 2020
last modified: 20.10.2020
"""

import numpy as np
import pandas as pd
import scipy.stats as sp
import os
from datetime import datetime
import colorcet as cc
from geographiclib.geodesic import Geodesic


def create_colordf(df):
    """
    Function to create a DataFrame containing a fixed color for each measurement station.

    :param df:  Pandas DataFrame containing all measurements, no index and column 'ID_Spectrometer'
    :return:    Pandas DataFrame with columns: 'ID_Spectrometer' and 'Color'

    created by: Nico Nachtigall
    at: September 2020
    last modified: 20.10.2020
    """
    np_siteID = df['ID_Spectrometer'].unique()
    # generate a dataframe to link a plotting color with a SiteID
    df_color = pd.DataFrame(columns=['ID_Spectrometer', 'Color'])
    for i in range(np.size(np_siteID)):
        df_color = df_color.append({'ID_Spectrometer': np_siteID[i], 'Color': cc.glasbey_light[i]}, ignore_index=True)
    return df_color


def timeFromDateHour(df):
    """
    Function to add a new column to the dataFrame df containing a date format
    :param df:  Pandas DataFrame, needs columns 'Date' and 'Hour'
    :return:    Pandas DataFrame, with additional column 'date_form'

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    index = df.index
    df = df.reset_index()
    df_time = pd.DataFrame()
    df_time['Hour'] = df['Hour'].apply(lambda x: int(x))
    df_time['minute'] = df['Hour'].apply(lambda x: (x * 60) % 60)
    df_time['secound'] = df['Hour'].apply(lambda x: (x * 3600) % 60)
    df_time['Date'] = df['Date']
    df['date_form'] = df_time.apply(lambda x: datetime.strptime(str(int(x.Date)) + str(int(x.Hour)) + str(int(x.minute)) + str(int(x.secound)), '%Y%m%d%H%M%S'), axis=1)
    return setindex(df, index)


def r2(x, y):
    # calculate r2 value
    return sp.pearsonr(x, y)[0] ** 2


def clusterby(df, clusterBy_str, **kwargs):
    """
    Function to generate averaged measurements
    Averaging is always done with respect to day and site

    :param df:              Pandas DataFrame, contains the measurements which should be averaged
    :param clusterBy_str:   String, column name on which the averaging should be done, normally 'Hour'
    :param kwargs:          optional
        int_max:            Number, averaging end value
        int_min:            Number, averaging start value
        int_delta:          Number, step size of the rolling averaging window
        drop_clu:           Boolean, drop cluster points with too less information
        drop_clu_info:      Dictionary, additional dropping information for cluster points
        win_size:           Number, averaging window size

    :return:                Pandas DataFrame with averaged values, columns remain the same as df

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    # reset index and save original index
    index = df.index.names
    df = df.reset_index()

    interval_max = kwargs.get('int_max', df[clusterBy_str].max())
    interval_min = kwargs.get('int_min', df[clusterBy_str].min())
    if interval_max is None:
        interval_max = df[clusterBy_str].max()
    if interval_min is None:
        interval_min = df[clusterBy_str].min()
    interval_delta = kwargs.get('int_delta', (interval_max - interval_min) / 30)
    drop_clusterpoints = kwargs.get('drop_clu', False)
    drop_clusterpoints_info = kwargs.get('drop_clu_info', {'drop': drop_clusterpoints, 'version': 'sigma', 'percent': 0.2})
    window_size = kwargs.get('win_size', interval_delta * 2)

    # check and calculate values for the window integral
    if window_size < interval_delta:
        print(
            'Window_size has to be bigger or equal than interval_delta. Window size is set to be equal to interval_delta')
        window_size = interval_delta

    win_add = (window_size - interval_delta) / 2 + interval_delta
    win_sub = (window_size - interval_delta) / 2

    # get steps
    steps = np.arange(interval_min, interval_max, interval_delta)

    # create empty data frame
    if np.isin(['ID_Location'], df.columns)[0]:
        df_clustered = pd.DataFrame(columns=np.append(df.columns, 'count')).drop(['ID_Location'], axis=1)
    else:
        df_clustered = pd.DataFrame(columns=np.append(df.columns, 'count'))

    # different grouping schema, if columns 'ID_Spectrometer' and/or 'Date' are not present
    if ((np.isin(['Date'], df.columns)[0]) & (np.isin(['ID_Spectrometer'], df.columns)[0])):
        df = df.set_index(['Date', 'ID_Spectrometer'])
        for s in steps:
            # get mean values over time
            df_temp = df.loc[(df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].groupby(
                level=[0, 1]).mean().reset_index()
            df_temp['count'] = \
            df.loc[(df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].groupby(
                level=[0, 1]).count().reset_index()[clusterBy_str]
            # adjust some values
            df_temp[clusterBy_str] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_clustered['Date'] = df_clustered['Date'].astype(int)
        df_final = get_month_year(df_clustered)

    elif np.isin(['ID_Spectrometer'], df.columns)[0]:
        df = df.set_index(['ID_Spectrometer'])
        for s in steps:
            # get mean values over time
            df_temp = df.loc[(df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].groupby(
                level=[0]).mean().reset_index()
            df_temp['count'] = \
            df.loc[(df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].groupby(
                level=[0]).count().reset_index()[clusterBy_str]
            # adjust some values
            df_temp[clusterBy_str] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_final = df_clustered

    elif np.isin(['Date'], df.columns)[0]:
        df = df.set_index(['Date'])
        for s in steps:
            # get mean values over time
            df_temp = df.loc[(df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].groupby(
                level=[0]).mean().reset_index()
            df_temp['count'] = \
            df.loc[(df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].groupby(
                level=[0]).count().reset_index()[clusterBy_str]
            # adjust some values
            df_temp[clusterBy_str] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_clustered['Date'] = df_clustered['Date'].astype(int)
        df_final = get_month_year(df_clustered)
    else:
        for s in steps:
            # get mean values over time
            df_temp = df.loc[
                (df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].mean().reset_index()
            df_temp['count'] = \
            df.loc[(df[clusterBy_str] < (s + win_add)) & (df[clusterBy_str] >= (s - win_sub))].count().reset_index()[
                clusterBy_str]
            # adjust some values
            df_temp[clusterBy_str] = s + (interval_delta / 2)
            df_clustered = df_clustered.append(df_temp, ignore_index=True)
        df_clustered['Date'] = df_clustered['Date'].astype(int)
        df_final = get_month_year(df_clustered)

    # remove all cluster Points which are calculated with too less data points
    if drop_clusterpoints_info['drop']:
        df_final = drop_ClusterPoints(df_final, drop_clusterpoints_info['version'], drop_clusterpoints_info['percent'])
    # reindex with the old index
    return setindex(df_final, index).drop('count', axis=1)


def drop_ClusterPoints(df, case, percent):
    """
    Function called from clusterby()
    Function to drop all rows where the averaged Point is not trustworthy
    this is defined by a threshold defining how many measurement Points are nessesary to trust the averaged Point
    the threshold is calculated based on a user defined percentage and either a given maximal information for an
    averaged measurement (in case of a small dataset) or by calculation of the maximal information (big dataset)
    :param df:      Pandas DataFrame, averaged measurements, need column 'count' (number of measurements per averaged point)
    :param case:    String: 'calculation' or Number: Maximal possible information for an averaged measurement
    :param percent: Number, [0,1]
    :return:        Pandas DataFrame, cleaned, same columns as df

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    if np.isin('count', df.columns, invert=True):
        print('Error dropping untrusted cluster points: "count" has to be a column')
        return df
    if case == 'calculation':
        threshold = get_thresehold_untrustedPoints(df, percent)
    else:
        threshold = case * percent
    return df[df['count'] > threshold]


def get_thresehold_untrustedPoints(df, per):
    """
    Function is called by drop_ClusterPoints()
    Function returns a threshold with which the averaged measurement points are dropped
    :param df:  Pandas DataFrame, containing averaged measurements
    :param per: Number, [0,1] percentage how much information is necessary
    :return:    Number, threshold

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    if np.isin('count', df.columns, invert=True):
        print('"count" as to be in column')
        return 0

    np_count = df['count'].values
    return np.max(np_count)*per


def get_2sigma(df):
    """
    Function called by drop_ClusterPoints()
    Function to calculate the threshold for dropping averaged points based on the Gaussian 2 sigma interval
    :param df:  Pandas DataFrame, averaged measurements, column 'count' is needed
    :return:    Number, threshold

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    if np.isin('count', df.columns, invert=True):
        print('"count" as to be in column')
        return 0

    np_count = df['count'].values
    num_points = np.sum(np_count)

    goal = 1
    i = 1
    # optimization to get threshold
    while goal > 0.9545:
        index = np.argwhere(np_count > i)
        goal = np.sum(np_count[index]) / num_points
        i = i + 1
    return i - 1  # -1 to undo the last step


def calibration(df_data_org, df_cali_org):
    """
    Function to calibrate measurement data
    :param df_data_org: Pandas DataFrame, containing all data,
                        columns needed: 'ID_Spectrometer', 'Date', 'xch4_ppm','xco2_ppm','xco_ppb'
    :param df_cali_org: Pandas DataFrame, containing the calibration values,
                        columns needed: 'ID_SpectrometerCalibration', 'EndDate', 'StartDate'
    :return:            Pandas DataFrame, with calibrated values, same columns as df_data_org

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    df_cali = df_cali_org.copy()
    # get full siteID
    df_cali['ID'] = df_cali['ID_SpectrometerCalibration'].apply(lambda x: x[-2:])
    np_siteID = df_data_org['ID_Spectrometer'].unique()
    for site in np_siteID:
        df_cali.loc[df_cali['ID'] == site[:2], 'ID'] = site
    # set all unknown enddates to inf
    df_cali.loc[df_cali['EndDate'].isnull(), 'EndDate'] = np.inf

    # calibrate data
    df_data = df_data_org.copy()
    for index, row in df_cali.iterrows():
        df_data.loc[(df_data['ID_Spectrometer'] == row.ID) & (df_data['Date'] >= row.StartDate) & (
                df_data['Date'] < row.EndDate), 'xch4_ppm'] = df_data.loc[(df_data['ID_Spectrometer'] == row.ID) & (
                df_data['Date'] >= row.StartDate) & (df_data[
                                                         'Date'] < row.EndDate), 'xch4_ppm'] / row.ch4_calibrationFactor
        df_data.loc[(df_data['ID_Spectrometer'] == row.ID) & (df_data['Date'] >= row.StartDate) & (
                df_data['Date'] < row.EndDate), 'xco2_ppm'] = df_data.loc[(df_data['ID_Spectrometer'] == row.ID) & (
                df_data['Date'] >= row.StartDate) & (df_data[
                                                         'Date'] < row.EndDate), 'xco2_ppm'] / row.co2_calibrationFactor
        df_data.loc[(df_data['ID_Spectrometer'] == row.ID) & (df_data['Date'] >= row.StartDate) & (
                df_data['Date'] < row.EndDate), 'xco_ppb'] = df_data.loc[(df_data['ID_Spectrometer'] == row.ID) & (
                df_data['Date'] >= row.StartDate) & (df_data[
                                                         'Date'] < row.EndDate), 'xco_ppb'] / row.co_calibrationFactor

    return df_data,df_cali

def timewindow_middle(np_timeseries, startPoint, time_interval_first, time_interval_sec):
    # Function to return data window of interest
    # function is called from calculate_smooth_background()
    index = np.where((np_timeseries >= startPoint - time_interval_first) & (
            np_timeseries < time_interval_sec + startPoint))

    return np_timeseries[index], index[0]

# Helper function for load_weather()
def f(x):
    return str(x)[:6]


def load_weather(df):
    """
    Function to load all LMU weather data which we could need
    Path where the weather data is stored is hard coded
    :param df:  Pandas DataFrame, needed to decide which data to load, columns needed: 'Date'
    :return:    Pandas DataFrame, containing weather information, index is number

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    # get all months
    D = np.vectorize(f)
    np_date = df['Date'].unique()
    np_month = np.unique(D(np_date))

    # get weather data for all months
    weather_folder = 'W:/data/LMU_wind_data/'

    df_weather = pd.DataFrame(columns= ['Date', 'Hour', 'temp2m', 'temp30m', 'humidTemp2m', 'humidTemp30m', 'windSpd30m', 'windDir30m', 'rain', 'globalRadiation', 'diffRadiation', 'pressure'])

    for month in np_month:
        for file in os.listdir(weather_folder):
            if file.startswith(month) & file.endswith('.txt'):
                df_tmpweather = pd.read_csv(os.path.join(weather_folder, file), header = 0, sep = ' ', names = ['year', 'month', 'day', 'Hour', 'minute', 'temp2m', 'temp30m', 'humidTemp2m', 'humidTemp30m', 'windSpd30m', 'windDir30m', 'rain', 'globalRadiation', 'diffRadiation', 'pressure'])
                # get correct structure
                df_tmpweather['Date'] = month + df_tmpweather['day'].astype(str).apply(lambda x: '0' + x if len(x)==1 else x  )
                df_tmpweather['Hour'] = df_tmpweather['Hour']+df_tmpweather['minute']/60 -0.78
                df_tmpweather = df_tmpweather.drop(['year','month','day','minute'], axis=1)
                df_weather = df_weather.append(df_tmpweather, ignore_index = True)
    return df_weather


def get_month_year(df):
    """
    Function to calculate year and month
    :param df:  Pandas DataFrame, column needed: 'Date'
    :return:    Pandas DataFrame with additional columns: 'year' and 'month'

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    index = df.index
    df = df.reset_index()
    if np.isin(['Date'],df.columns)[0]:
        df['month'] = df['Date'].apply(lambda x: x - round(x, -4)).apply(lambda x: round(x, -2)/100)
        df['year'] = df['Date'].apply(lambda x: round(x/10000))
    else:
        print('Column "date" is missing. No calculation possible.')

    df = setindex(df, index)
    return df


def setindex(df, column_array):
    """
    Helper function to set the index of the DataFrame to the columns stored in the input array
    :param df:              Pandas DataFrame
    :param column_array:    Numpy Array, containing column names of df which should be set as index
    :return:                Pandas DataFrame with chosen columns as index

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """
    if column_array[0] is None:
        return df
    df = df.set_index(column_array)
    if np.isin(['index'], df.columns)[0]:
        df_fin = df.drop(['index'], axis = 1)
    elif np.isin(['index_0'], df.columns)[0]:
        df_fin = df.drop(['index_0'], axis = 1)
    else:
        df_fin = df.copy()
    return df_fin


# ----- Functions for the location calculation

def calc_dist(df, x):
    """
    Called from gen_df_geo()
    Function to calculate the distance and angle between measurement locations loc_1 and loc_2

    :param df:  Pandas DataFrame,
    :param x:   Pandas Data Series (one row of a DataFrame), columns: 'Location_1', 'Location_2'
    :return:    Pandas Data Series with additional columns 'angle', 'distance_km'

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    df_reset = df.reset_index()

    loc_1 = x['Location_1']
    loc_2 = x['Location_2']

    df_loc1 = df_reset.loc[df_reset['ID_Location'] == loc_1]
    df_loc2 = df_reset.loc[df_reset['ID_Location'] == loc_2]

    lat1 = df_loc1.Coordinates_Latitude.unique()
    lon1 = df_loc1.Coordinates_Longitude.unique()
    lat2 = df_loc2.Coordinates_Latitude.unique()
    lon2 = df_loc2.Coordinates_Longitude.unique()

    # Distance calculation
    x['distance_km'] = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)['s12'] / 1000  # to get [km]
    # bearing calculation
    angle = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)['azi1']
    if angle < 0:
        x['angle'] = 360 + angle
    else:
        x['angle'] = angle
    return x





def gen_df_geo(df):
    """
    Function to generate a DataFrame which contains all possible location combinations and calculates the distance
    and angle between them
    :param df:  DataFrame, needs columns ['ID_Location', 'Coordinates_Latitude', 'Coordinates_Longitude']
    :return:    DataFrame with columns: 'Location_1', 'Location_2', 'angle', 'distance_km'

    created by: Nico Nachtigall, September 2020
    last modified: 20.10.2020
    """

    # drop unknown location
    df = df.drop(index=df.loc[df['ID_Location'] == 'NK'].index)

    # get all possible location combinations
    np_allCombinations = np.array(np.meshgrid(df['ID_Location'].values, df['ID_Location'].values)).T.reshape(-1, 2)
    # initialise dataframe with all possible combinations
    df_distance = pd.DataFrame(np_allCombinations, columns=['Location_1', 'Location_2'])
    # calculate distance of all possible combinations
    df_distance = df_distance.apply(lambda x: calc_dist(df, x), axis=1)

    return df_distance



