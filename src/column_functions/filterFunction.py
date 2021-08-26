"""
Project Description:
This program is part of the master thesis of Nico Nachtigall. It contains all functions needed to filter the column
measurements.

Author: Nico Nachtigall
created: September 2020
last modified: 20.10.2020
"""


import numpy as np
from .helperFunction import helperfunction as hp   # self written .py file
from scipy.optimize import curve_fit
import scipy.stats as sp


def filterData(data, fvsi_thold, sia_thold, sza_thold, step_size, o2_error, flag):
    """
    Function to filter on physical behavior. Based on Jias fitler approach.
    Input:
    :param data:        Pandas DataFrame, containing Data of one day and station
                            need columns: 'Hour', 'sia_AU', 'asza_deg', 'xo2_error', 'flag', 'fvsi'
    :param fvsi_thold:  Number, fractional variation in solar intensity < the value, default: 5
    :param sia_thold:   Number, solar intensity average > value, default: 0.4
    :param sza_thold:   Number, solar zenith angle < value, default: 75
    :param step_size:   Number, default: 0.1
    :param o2_error:    Number, default: 0.0005
    :param flag:        0 or 1, if 0 the flag parameter is not considered for filtering (except for no. 24 xair,
			which shows an oversaturated signal); if 1, only measurements with flag <3 remain

    Output:
    :return: Pandas DataFrame, containing filtered values

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    sia_ref = data[
        'sia_AU'].values.copy()  # copy is needed here otherwise the values in the database are changed when sia_ref is modifyed
    time = data['Hour'].values

    # solar intensity reference values are calculated. Values have to be above those reference values
    m = sia_ref.max() * step_size
    for ii in range(0, sia_ref.size - 2):
        dt = time[ii + 1] - time[ii]
        if (sia_ref[ii] - sia_ref[ii + 1] >= m * dt):
            sia_ref[ii + 1] = sia_ref[ii] - m * dt

    for ii in range(sia_ref.size - 1, 1, -1):
        dt = time[ii] - time[ii - 1]
        if (sia_ref[ii] - sia_ref[ii - 1] >= m * dt):
            sia_ref[ii - 1] = sia_ref[ii] - m * dt

    # Filter step
    if (flag == 1):
        df_ok = data.loc[
            (data['sia_AU'] >= sia_ref * sia_thold) & (data['flag'] < 3) & (data['fvsi'] <= fvsi_thold) & (
                        data['asza_deg'] <= sza_thold) & (data['xo2_error'] < o2_error)]
    else:
        df_ok = data.loc[
            (data['sia_AU'] >= sia_ref * sia_thold) & (data['flag'] != 24) & (data['fvsi'] <= fvsi_thold) & (
			data['asza_deg'] <= sza_thold) & (data['xo2_error'] < o2_error)]
    return df_ok


def getIndexIntervall(x, num, check_day=False):
    """
    Helper function for filter_intervall(df)
    Function return index values which should be deleted based on their interval size
    check_day = True, whole day is removed if an interval of size num does not exists
    check_day = False, intervals which do not contain num elements will be removed

    Input:
    :param x: numpy array
    :param num: number, interval size for which to check
    :param check_day: boolean, changes the behavior of the function

    Output:
    :return: numpy array, containing the index of all values, which should be removed

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    np_int = np.diff(x) >= num
    # this if cause is called if a day is checked for continuous measurements, if one interval is found which satisfies
    # the conditions no points will be dropped
    if check_day:
        if np.where(np_int == True)[0].size != 0:
            return np.array([])
    np_indexBigGap = np.where(np_int == False)[0]
    np_badindex = np.array([])
    for i in np_indexBigGap:
        # check for end and if the next interval is valide
        if ((i == np_indexBigGap[-1]) or (np.isin(i + 1, np_indexBigGap, invert=True))):
            np_badindex = np.append(np_badindex, np.arange(x[i], x[i + 1] + 1, 1))
        else:
            np_badindex = np.append(np_badindex, np.arange(x[i], x[i + 1], 1))
    return np_badindex


def filter_intervall(df, num, gap, check_day=False):
    """
    normally called by: filter_DataStat()
    Function to delete measuring intervals (which are defined as measurments between measuring gaps of time > 'gab')
    check_day = True, whole day is removed if an interval of size num does not exists
    check_day = False, intervals which do not contain num elements will be removed

    Input:
    :param df:          Pandas DataFrame, need columns: 'Date', 'ID_Spectrometer', 'Hour'
    :param num:         Number, interval size
    :param gap:         Number, time in second which defines a gap
    :param check_day:   Boolean

    Output:
    :return:            Pandas DataFrame, filtered Data

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    df_reset = df.reset_index().drop(columns=['Date', 'ID_Spectrometer'])
    np_diff = np.diff(df_reset['Hour'].values) # get time difference between measurements
    np_indexGap = np.append(0, np.append((np.argwhere(np_diff > gap)), np_diff.size))
    np_indexToBeDroped = getIndexIntervall(np_indexGap, num, check_day) # get index which measurements should be dropped
    return df_reset.drop(np_indexToBeDroped)


def filter_day_alone(df):
    """
    normally called by: filter_DataStat()
    Function filters all days on which just one site was measuring
    Input:
    :param df: Pandas DataFrame, Measurements of one day, need Index to be 'Date', 'ID_Spectrometer'

    Output:
    :return: Pandas DataFrame

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    if df.index.get_level_values(1).unique().values.shape[0]>1:
        return df


def zscore_move(df, column, interval, stepsize, threshold):
    """
    normally called by: filter_DataStat()
    Function to remove outliers
    for outliers detection a zscore algorithmus is used based on a rolling window

    Input:
    :param df:          Pandas DataFrame, containing measurements of one day and one station
    :param column:      String, label of the column which should be filtered
    :param interval:    Number, rolling window size in h
    :param stepsize:    Number, rolling window step in h
    :param threshold:   Number, zscore threshold above which the point is detected as outlier

    Output:
    :return:            Pandas DataFrame, where all outlier rows are removed, no index

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    df_reset = df.reset_index().drop(columns=['Date', 'ID_Spectrometer'])
    np_timexch4 = df_reset[['Hour', column]].values
    start_time = np_timexch4[:, 0].min()
    end_time = np_timexch4[:, 0].max()

    s = start_time

    np_storeDelete = np.array([])
    while s < end_time:  # rolling window

        # use full interval by default
        interval_first = interval / 2
        interval_secound = interval / 2
        # check full interval can be used
        if s < start_time + interval / 2:
            # calculate max possible interval
            interval_first = s - start_time
        if s > end_time - interval / 2:
            # calculate max possible interval
            interval_secound = end_time - s

        # get window
        time_w, index = hp.timewindow_middle(np_timexch4[:, 0], s, interval_first, interval_secound)

        # get values
        np_inter = np_timexch4[index, 1]

        # to make sure to have enough points for calculation, 100 is chosen randomly
        if len(np_inter) > 100:
            np_zscore = sp.zscore(np_inter)
            np_indexDelete = np.where(np.abs(np_zscore) > threshold)[0]

            np_storeDelete = np.append(np_storeDelete, time_w[np_indexDelete], axis=0)

        s = s + stepsize

    np_TimeDelete = np.unique(np_storeDelete)

    if len(np_TimeDelete) == 0:  # no outliers were detected
        return df_reset
    else:
        return df_reset.set_index('Hour').drop(np_TimeDelete).reset_index()



def filter_DataStat(df, **kwargs):
    """
    Function to filter measurements based on data statistics
    with in this function the following filter are called:
      * Outlier filter
      * Interval filter
      * Average points to remove noise
      * delete measurement series if a site has measured too less Points per day in a row
      * delete all Points where just one site has measured

    Input:
    :param df:      Pandas DataFrame, containing all measurement data, index: 'Date', 'ID_Spectrometer'
    :param kwargs:  optional parameter
        clu_int:    Number, averaging interval, default: 0.25 [h]
        clu_drop:   Boolean, averaging point should be dropped if it consists of too less measurements, default: False
        clu_win:    Number, averaging window size, default: clu_int*2 [h]
        clu_str:    Number, time when the averaging should start each day, default: None [h]
        clu_end:    Number, time when the averaging should end, default: None [h]
        gas:        String, gas for which to filter ['xch4', 'xco2' or 'xco'], default: 'xch4'
        drop_clu_info:  Dictionary, containing the description of how to drop averaging points, similar to clu_drop
        case:       List, containing the filter steps which should be performed, just needed if not all steps should be
                    performed, can contain: 'outlier', 'interval', 'rollingMean', 'continuous', 'singleDay'

    Output:
    :return:        Pandas DataFrame, index 'Date', 'ID_Spectrometer'

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    clu_int = kwargs.get('clu_int', 0.25)
    clu_drop = kwargs.get('clu_drop', False)
    clu_win = kwargs.get('clu_win', clu_int * 2)
    clu_start = kwargs.get('clu_str', None)
    clu_end = kwargs.get('clu_end', None)
    gas = kwargs.get('gas', 'xch4')
    drop_clusterpoints_info = kwargs.get('drop_clu_info',
                                         {'drop': clu_drop, 'version': 'sigma', 'percent': 0.2})
    filter_case = kwargs.get('case', ['outlier', 'interval', 'rollingMean', 'continuous', 'singleDay'])

    if gas == 'xco':
        column = 'xco_ppb'
    elif gas == 'xco2':
        column = 'xco2_ppm'
    elif gas == 'xch4':
        column = 'xch4_ppm'
    else:
        print('ERROR: No valid gas is set. Set gas to "xch4", "xco" or "xco2".')
    # Filter Outlier
    if 'outlier' in filter_case:
        df_filtered = df.groupby(level=[0, 1]).apply(zscore_move, column, 2, 1, 2.58).reset_index(level=[2],
                                                                                                     drop=True)
    else:
        df_filtered = df.copy()
    # filter interval
    if 'interval' in filter_case:
        df_filtered = df_filtered.groupby(level=[0, 1]).apply(filter_intervall, 12, 0.005).reset_index(level=2,
                                                                                                          drop=True)
    # Average points to remove noise
    if 'rollingMean' in filter_case:
        df_filtered = hp.clusterby(df_filtered, 'Hour',
                                   int_delta=clu_int, drop_clu_info=drop_clusterpoints_info, int_max=clu_end,
                                   int_min=clu_start,
                                   win_size=clu_win).sort_index()

    # filter all days with no 1h continous measurements: filter_intervall (function),
    #   1/clu_int (number of clusterpoints needed in an hour to have continuous measurements),
    #   clu_int+clu_int/2 (allowed gab size between two points, bigger than a normal gab but smaller than two)
    if 'continuous' in filter_case and 'rollingMean' in filter_case:
        df_filtered = df_filtered.groupby(['Date', 'ID_Spectrometer']).apply(filter_intervall, int(1 / clu_int),
                                                                             clu_int + clu_int / 2, True).reset_index(
            level=[2], drop=True)
    elif 'continuous' in filter_case:
        print(
            'Error: Continuous filter step could not be performed, rolling mean step is needed in addition! Filtering is canceled!')
        return df_filtered
    
    # filter all days with just one site measuring
    if 'singleDay' in filter_case and 'rollingMean' in filter_case:
        df_filtered = df_filtered.groupby(['Date'], as_index=False).apply(filter_day_alone)#.reset_index(level=0,drop=True)
    elif 'singleDay' in filter_case:
        print(
            'Error: Single day filter step could not be performed, rolling mean step is needed in addition! Filtering is canceled!')
        return df_filtered

    return df_filtered


################## Air Mass Correction

def func(x, a, b, c):
    """
    fitting function for air mass correction
    called from correct()

    Input:
    :param x: Number, elevation angle
    :param a: Number, fitting parameter 1
    :param b: Number, fitting parameter 2
    :param c: Number, fitting parameter 3

    Output:
    :return: Number, calculated measurement

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """


    return a * np.abs(x) ** 3 + b * np.abs(x) + c


def correct(df_original, calculation=True):
    """
    called from airmass_corr()
    Function to fit and correct 'xch4_ppm_sub_mean' values from air mass dependency

    Input:
    :param df_original: Pandas DataFrame, all measurements, needed column: 'xch4_ppm_sub_mean'
    :param calculation: Boolean, Ture if the parameter should be calculated, False if saved should be used

    Output:
    :return:            Pandas DataFrame, corrected values are stored in column: 'xch4_ppm_corr'

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """
    # make copy to not change the original input DataFrame
    df = df_original.copy()

    # value shift to get not in trouble with devision thru zero
    df['xch4_ppm_sub_mean'] = df['xch4_ppm_sub_mean'] + 1

    # curve fitting -calculate values from big dataset
    if calculation:
        params, params_covariance = curve_fit(func, df['elevation_angle'], df['xch4_ppm_sub_mean'])
    else:
        # saved values when using small dataset
        params = [-5.39*(10**-10), 9.09*(10**-5), 9.97*(10**-1)]

    # correction
    x = df['elevation_angle'].values
    y_pred = func(x, params[0], params[1], params[2])
    y_real = df['xch4_ppm_sub_mean'].values
    df['xch4_ppm_sub_mean_corr'] = y_real / y_pred - 1

    # undo changes
    df['xch4_ppm_sub_mean'] = df['xch4_ppm_sub_mean'] - 1

    # correction of absolute measuremts
    df['mean'] = df['xch4_ppm'] - df['xch4_ppm_sub_mean']
    df['xch4_ppm'] = df['mean'] + df['xch4_ppm_sub_mean_corr']

    return df.drop(['mean','xch4_ppm_sub_mean_corr'], axis=1)


def airmass_corr(df, **kwargs):
    """
    Function for air mass correction of measurements of methane
    Input:
    :param df:      Pandas DataFrame, containing all measurements,
                        columns needed: 'Hour', 'xch4_ppm_sub_mean', 'elevation_angle', 'xch4_ppm'
    :param kwargs:
        clc:        Boolean, true when new calculation is wished, false when literature parameter should be used
        big_dataSet: Boolean, true when the whole dataset is used and the parameter can be calculated, false if just single
                    days are used, default: True

    Output:
    :return:        Pandas DataFrame, correced values are stored in columns: 'xch4_ppm_sub_mean_corr', 'xch4_ppm_corr'

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """
    calculate = kwargs.get('clc', True)
    big_dataSet = kwargs.get('big_dataSet', True)

    if calculate:
        #if big_dataSet:
            # split dataset if whole dataset is used
            #df_corr = correct(df.loc[:20190801], True)
            #df_corr = df_corr.append(correct(df.loc[20190801:], True)).sort_index()
        #else:
            # use defined parameter if just a small dataset is used
        #    df_corr = correct(df, False)
        df_corr = correct(df, False)
    else:
        df_corr = df.copy()
        parameter = [-7.05 * (10 ** (-9)), 5.34 * (10 ** (-6)), 1.00059]
        x = df_corr['asza_deg'].values
        corr = func(x, parameter[0], parameter[1], parameter[2])
        df_corr['xch4_ppm_corr'] = df_corr['xch4_ppm'] / corr
        df_corr['xch4_ppm'] = df_corr['xch4_ppm_corr'] - (
                    df_corr['xch4_ppm'] - df_corr['xch4_ppm_sub_mean'])
        df_corr = df_corr.drop(['xch4_ppm_corr'], axis=1)

    return df_corr
