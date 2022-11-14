"""
Project Description:
This program is part of the master thesis of Nico Nachtigall. It contains all functions needed to filter the column
measurements.

Author: Nico Nachtigall
created: September 2020
last modified: 20.10.2020
"""


import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from src.dataframe_processing import utility_functions
from src import utils


def apply_statistical_filter(
    df: pd.DataFrame,
    gas: str,
    cluster_output_step_size: float = 15,
    cluster_window_size: float = 30,
    filter_cases: list[str] = [
        "outlier",
        "interval",
        "rollingMean",
        "continuous",
        "singleDay",
    ],
) -> pd.DataFrame:
    """
    Function to filter measurements based on data statistics with in this
    function the following filter are called:
      * Outlier filter
      * Interval filter
      * Average points to remove noise
      * delete measurement series if a site has measured too few points
        per day in a row
      * delete all points where just one site has measured

    Input:
    :param df:                          DataFrame containing all measurement data, index: 'Date',
                                        'ID_Spectrometer'
    :param gas:                         gas for which to filter ['xch4', 'xco2' or 'xco']
    :param cluster_output_step_size:    Averaging interval in minutes
    :param cluster_window_size:         Averaging window size in minutes
    :param drop_clusterpoints_info:     Dictionary, containing the description of
                                        how to drop averaging points, similar to
                                        clu_drop
    :param filter_cases:                List containing the filter steps which
                                        should be performed, just needed if not
                                        all steps should be performed, can contain:
                                        'outlier', 'interval', 'rollingMean',
                                        'continuous', 'singleDay'

    Output:
    :return:        DataFrame, index 'Date', 'ID_Spectrometer'

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    utils.functions.assert_df_index(df, ["Date", "ID_Spectrometer"])
    assert gas in ["xco", "xco2", "xch4"]

    # TODO: Clean up, improve
    if "outlier" in filter_cases:
        column = gas + "_" + utils.constants.UNITS[gas[1:]]
        df = (
            df.groupby(level=[0, 1])
            .apply(_zscore_move, column)
            .reset_index(level=[2], drop=True)
        )

    # TODO: Clean up, improve
    if "interval" in filter_cases:
        df = (
            df.groupby(level=[0, 1])
            .apply(_filter_interval, 12, 0.005)
            .reset_index(level=2, drop=True)
        )

    # TODO: Clean up, improve
    # apply rolling mean to remove noise
    if "rollingMean" in filter_cases:
        df = utility_functions.cluster_by(
            df,
            interval_delta=round(cluster_output_step_size / 60, 6),
            drop_clusterpoints_info={"drop": True, "version": 104, "percent": 0.2},
            window_size=round(cluster_window_size / 60, 6),
            interval_max=18,
            interval_min=4,
        ).sort_index()

    # TODO: Clean up, improve
    # filter all days with no 1h continous measurements: filter_interval
    # (function), 1/clu_int (number of clusterpoints needed in an hour to
    # have continuous measurements), clu_int+clu_int/2 (allowed gap size
    # between two points, bigger than a normal gap but smaller than two)
    if "continuous" in filter_cases:
        assert "rollingMean" in filter_cases
        df = df.groupby(["Date", "ID_Spectrometer"]).apply(
            _filter_interval,
            int(1 / cluster_output_step_size),
            1.5 * cluster_output_step_size,
            True,
        )
        try:
            df = df.reset_index(level=[2], drop=True)
        except:
            pass

    # TODO: Clean up, improve
    # filter all days with just one site measuring
    if "singleDay" in filter_cases:
        assert "rollingMean" in filter_cases
        df = df.groupby(["Date"], as_index=False).apply(_filter_single_day)

    return df


def _getIndexInterval(x: np.array, num: float, check_day=False) -> np.array:
    """
    Helper function for filter_intervall(df)
    Function return index values which should be deleted based on their interval size
    check_day = True, whole day is removed if an interval of size num does not exists
    check_day = False, intervals which do not contain num elements will be removed

    Input:
    :param x
    :param num:         interval size for which to check
    :param check_day:   changes the behavior of the function

    Output:
    :return:            array containing the index of all values, which should be removed

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
        if (i == np_indexBigGap[-1]) or (np.isin(i + 1, np_indexBigGap, invert=True)):
            np_badindex = np.append(np_badindex, np.arange(x[i], x[i + 1] + 1, 1))
        else:
            np_badindex = np.append(np_badindex, np.arange(x[i], x[i + 1], 1))
    return np_badindex


def _filter_interval(df: pd.DataFrame, num: float, gap: float, check_day=False):
    """
    normally called by: filter_DataStat()
    Function to delete measuring intervals (which are defined as measurments between measuring gaps of time > 'gab')
    check_day = True, whole day is removed if an interval of size num does not exists
    check_day = False, intervals which do not contain num elements will be removed

    Input:
    :param df:          DataFrame, need columns: 'Date', 'ID_Spectrometer', 'Hour'
    :param num:         interval size
    :param gap:         time in second which defines a gap
    :param check_day:

    Output:
    :return:            DataFrame, filtered Data

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """
    utils.functions.assert_df_columns(df, ["Date", "ID_Spectrometer", "Hour"])

    df = df.copy().reset_index().drop(columns=["Date", "ID_Spectrometer"])

    np_diff = np.diff(df["Hour"].values)  # get time difference between measurements
    np_indexGap = np.append(0, np.append((np.argwhere(np_diff > gap)), np_diff.size))
    np_indexToBeDroped = _getIndexInterval(
        np_indexGap, num, check_day
    )  # get index which measurements should be dropped
    return df.drop(np_indexToBeDroped)


def _filter_single_day(df: pd.DataFrame):
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

    if df.index.get_level_values(1).unique().values.shape[0] > 1:
        return df


def _zscore_move(
    df: pd.DataFrame,
    column: str,
    interval: float = 2,
    stepsize: float = 1,
    threshold: float = 2.58,
) -> pd.DataFrame:
    """
    normally called by: filter_DataStat()
    Function to remove outliers
    for outliers detection a zscore algorithmus is used based on a rolling window

    Input:
    :param df:          DataFrame, containing measurements of one day and one station
    :param column:      label of the column which should be filtered
    :param interval:    rolling window size in h
    :param stepsize:    rolling window step in h
    :param threshold:   zscore threshold above which the point is detected as outlier

    Output:
    :return:            Pandas DataFrame, where all outlier rows are removed, no index

    created by: Nico Nachtigall
    on: September 2020
    last modified: 20.10.2020
    """

    df = df.copy()

    df_reset = df.reset_index().drop(columns=["Date", "ID_Spectrometer"])
    np_timexch4 = df_reset[["Hour", column]].values
    start_time = np_timexch4[:, 0].min()
    end_time = np_timexch4[:, 0].max()

    s = start_time
    np_storeDelete = np.array([])

    # rolling window
    while s < end_time:
        # use full interval by default
        interval_first = interval / 2
        interval_second = interval / 2

        # check full interval can be used
        if s < start_time + interval / 2:
            # calculate max possible interval
            interval_first = s - start_time

        if s > end_time - interval / 2:
            # calculate max possible interval
            interval_second = end_time - s

        # get window
        time_w, index = utility_functions.timewindow_middle(
            np_timexch4[:, 0], s, interval_first, interval_second
        )

        # get values
        np_inter = np_timexch4[index, 1]

        # to make sure to have enough points for calculation, 100 is chosen randomly
        if len(np_inter) > 100:
            np_zscore = scipy_stats.zscore(np_inter)
            np_indexDelete = np.where(np.abs(np_zscore) > threshold)[0]

            np_storeDelete = np.append(np_storeDelete, time_w[np_indexDelete], axis=0)

        s += stepsize

    np_TimeDelete = np.unique(np_storeDelete)

    if len(np_TimeDelete) == 0:  # no outliers were detected
        return df_reset
    else:
        return df_reset.set_index("Hour").drop(np_TimeDelete).reset_index()
