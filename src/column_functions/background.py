"""
Project Description:
This program is part of the master thesis of Nico Nachtigall. It contains all functions needed to calculate the global
background of the column measurements.

Author: Nico Nachtigall
created: September 2020
last modified: 19.10.2020
"""

from scipy.signal import butter, filtfilt
from .helperFunction import helperfunction as hp
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
import pandas as pd
import numpy as np


def calculate_Background(df, back_type='smooth', **kwargs):
    ####
    # Function to calculate global background
    # three different backgroundtypes are implemented:
    #    'smooth': takes lowest points and uses lowpass filter to smooth the shape
    #    'static': takes the lowest point per day and take this as constant background
    #    'low_points': takes the lowest points per time step as background
    #
    # input:
    #     df: DataFrame
    #     back_type = <'smooth'>, 'static', 'low_points'
    #     gas = 'xch4', 'xco', 'xco2'
    #     cluster_start = double [h]
    #     cluster_interval = double [h]
    # return:
    #     df with additional columns: ['gas+_fixed_background','gas+_en_fixed']
    #     'gas+_fixed_background' contains background value
    #     'gas+_en_fixed' contains measurement minus background

    config_default = {'general': {'gas': 'xch4',
                                  'cluster_start': 8,
                                  'cluster_interval': 16,
                                  'shape': 'min',
                                  'delete_single': True,
                                  'not_shift': True

                                  },
                      'smooth': {'order': 1,
                                 'cutoff': 1 / 6,
                                 'offset': 0,
                                 'interval': 4,  # in h size of rolling window
                                 'extrapolate': True,  # use extrapolation for better edge performance
                                 # threshold which ratio of data has to be above background
                                 'threshold_quantile': 0.95,
                                 'filter_version': 'kaiser',  # choose methode for low pass filter
                                 'kaiser_level': 8
                                 # choose intensity of kaiser window, 0..inf, 0: all values are equally weighted,
                                 # inf: center point as all power
                                 },
                      'limit_std': {'rolling_window_size': 10,
                                    'value_limit': 0.1,
                                    'std_window': 15,
                                    'std_limit': 0.5
                                    }
                      }
    config = kwargs.get('config', config_default)

    # get variables
    try:
        gas = config['general']['gas']
        shape = config['general']['shape']
        delete_single = config['general']['delete_single']
        threshold_quantile = config['smooth']['threshold_quantile']
        offset = config['smooth']['offset']
        not_shift = config['general']['not_shift']
    except:
        gas = 'xch4'
        shape = 'min'
        delete_single = True
        offset = 0
        threshold_quantile = 1
        not_shift = True

    # check for correct gas
    if gas == 'xco':
        column = 'xco_ppb'
    elif gas == 'xco2':
        column = 'xco2_ppm'
    elif gas == 'xch4':
        column = 'xch4_ppm'
    else:
        print('ERROR: No valid gas is set. Set gas to "xch4", "xco" or "xco2".')
        return df

    index = df.index
    df = df.reset_index()

    # delete all points with just one station measuring
    if delete_single:
        df_count = df.groupby(['Date', 'Hour']).count()
        df_addcount = df.set_index(['Date', 'Hour']).join(
            df_count[['ID_Spectrometer']].rename(columns={'ID_Spectrometer': 'count'})).reset_index()
        df = df_addcount.loc[df_addcount['count'] > 1].copy()
        df = df.drop(columns=['count'])

    # calculate lowest Points
    df_lowestPoints = df.groupby(['Date', 'Hour']).min().reset_index()

    # get all dates
    dates = df_lowestPoints['Date'].unique()
    # initialise empty Dataframe
    df_store = pd.DataFrame(columns=['Date', 'Hour', gas + '_fixed_background'])

    # choose the right background calculation strategy
    if back_type == 'smooth':
        for date in dates:

            # look at every station shape
            if shape == 'all':
                df_store_day = pd.DataFrame(columns=['ID_Spectrometer', 'Hour', gas + '_fixed_background'])

                # get curve of every spectrometer
                for id_spec, group in df.loc[df['Date'] == date].copy().groupby(['ID_Spectrometer']):
                    df_temp_spectrometer = calculate_smooth_background_middle(group.copy(), config, column)
                    df_temp_spectrometer['ID_Spectrometer'] = id_spec
                    df_store_day = df_store_day.append(df_temp_spectrometer, ignore_index=True)

                # get mean resulting curve -> curve of the day
                df_temp_mean = df_store_day.drop(columns='ID_Spectrometer').groupby('Hour', as_index=False).mean()

                # smooth the resulting curve, otherwise the curve consist of many inconsistencys
                df_temp_day = calculate_smooth_background_middle(
                    df_temp_mean.rename(columns={gas + '_fixed_background': column}), config, column)

                # shift resulting curve under lowest points
                np_background = df_temp_day[gas + '_fixed_background'].values
                np_lowestPoints = df_lowestPoints.loc[df_lowestPoints['Date'] == date][column].values
                y_shift = np.nanquantile(np_background - np_lowestPoints, threshold_quantile)
                if not_shift:
                    y_shift = 0
                np_storefitted = np_background - y_shift - offset
                df_temp_day[gas + '_fixed_background'] = np_storefitted
            else:
                df_temp_day = calculate_smooth_background_middle(
                    df_lowestPoints.loc[df_lowestPoints['Date'] == date].copy(),
                    config, column)
            df_temp_day['Date'] = date
            df_store = df_store.append(df_temp_day)
    elif back_type == 'static':
        for date in dates:
            # get lowest point per day
            min_value = df_lowestPoints.loc[df_lowestPoints['Date'] == date].min()[column]
            df_temp_day = df_lowestPoints.loc[df_lowestPoints['Date'] == date][['Hour']]
            df_temp_day['Date'] = date
            df_temp_day[gas + '_fixed_background'] = min_value
            df_store = df_store.append(df_temp_day)
    elif back_type == 'low_points':
        df_store = df_lowestPoints[['Date', 'Hour', column]].rename(columns={column: gas + '_fixed_background'})
    else:
        print(
            'ERROR: No valid background calculation method is used. Set back_type to "smooth", "static" or "low_points".')
        return hp.set_index(df, index)

    # join the results
    df_background = df.set_index(['Date', 'Hour']).join(df_store.set_index(['Date', 'Hour'])[gas + '_fixed_background'])
    # calculate and save the corrected measurements
    if gas == 'xch4':
        df_background[gas + '_en_fixed'] = df_background[column].sub(df_background[gas + '_fixed_background'])
    elif gas == 'xco2':
        df_background[gas + '_en_fixed'] = df_background[column].sub(df_background[gas + '_fixed_background'])
    elif gas == 'xco':
        df_background[gas + '_en_fixed'] = df_background[column].sub(df_background[gas + '_fixed_background'])

    return df_background


def extrapolation(np_bkgMatrix, stepsize, window_size):
    """
    Function to linear extrapolate day shape
        fits a linear curve to the edges of the day shape

        input:  np_bkgMatrix size = [n,2] first column are timesteps and second column measured concentrations
                stepsize: normal timedistance between measurements
                window_size: size of rolling window
        output: np_nkgMatrixAdd size = [n+window_size,2] first column are timesteps and second column measured concentrations
    """

    def func(x, a, b):
        # fitting function
        return a * x + b

    x_all = np_bkgMatrix[:, 0]
    y_all = np_bkgMatrix[:, 1]
    # extrapolate the beginning of the day
    x = np.concatenate(x_all[np.argwhere(x_all < (min(x_all) + window_size / 2))])
    y = np.concatenate(y_all[np.argwhere(x_all < (min(x_all) + window_size / 2))])
    x_beg = np.arange(min(x) - (window_size / 2 - np.round((window_size / 2) % stepsize, 6)), min(x) - (stepsize / 2),
                      stepsize)
    if ((len(x) > 1) & (len(y) > 1)):  # at least two points are needed for extrapolation
        params, params_covariance = curve_fit(func, x, y)
        y_beg = func(x_beg, params[0], params[1])
        np_nkgMatrixAdd = np.append(np.stack((x_beg, y_beg), axis=-1), np_bkgMatrix, axis=0)
    else:
        np_nkgMatrixAdd = np_bkgMatrix

    # extrapolate the end of the day
    x = np.concatenate(x_all[np.argwhere(x_all > (max(x_all) - window_size / 2))])
    y = np.concatenate(y_all[np.argwhere(x_all > (max(x_all) - window_size / 2))])
    x_end = np.arange(max(x) + stepsize, max(x) + window_size / 2 + stepsize / 2,
                      stepsize)  # plus stepsize is important otherwise max(x) will be calculated as well and then it's double
    if ((len(x) > 1) & (len(y) > 1)):
        params, params_covariance = curve_fit(func, x, y)
        y_end = func(x_end, params[0], params[1])
        np_nkgMatrixAdd = np.append(np_nkgMatrixAdd, np.stack((x_end, y_end), axis=-1), axis=0)

    return np_nkgMatrixAdd


def butter_lowpass_filter(data, cutoff, fs, order):
    # Function to Filter Data for given window
    # function is called from calculate_smooth_background()
    # input:
    #    data = np array
    #    cutoff = frequence above which should be cutoff
    #    fs = sampling frequency, must be same unit as cutoff e.g. 1/h or 1/s
    #    order = filter order

    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    # Get the filter coefficients
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y





def calculate_smooth_background_middle(df, config, column):
    ####
    # Function to calculate smooth background
    # function called from calculate_Background()
    # df contains just measurements per day
    ####
    try:
        gas = config['general']['gas']
        cluster_start = config['general']['cluster_start']
        cluster_interval = config['general']['cluster_interval']
        cutoff = config['smooth']['cutoff']
        order = config['smooth']['order']
        offset = config['smooth']['offset']
        interval = config['smooth']['interval']
        extrapolate = config['smooth']['extrapolate']
        threshold_quantile = config['smooth']['threshold_quantile']
        filter_version = config['smooth']['filter_version']
        level = config['smooth']['kaiser_level']
        not_shift = config['general']['not_shift']
        shape = config['general']['shape']
    except:
        gas = column[:4]
        if gas == 'xco_':
            gas = 'xco'
        cluster_start = 8
        cluster_interval = 0.25
        cutoff = 1 / 6
        order = 1
        offset = 0
        interval = 4
        extrapolate = True
        threshold_quantile = 1
        filter_version = 'butter'
        level = 8  # level for kaiser window
        not_shift = False
        shape = 'min'

    # make sure the shapes will not be shifted normaly
    if ((shape == 'all') & (not_shift == True)):
        not_shift = True
    else:
        not_shift = False

    np_timexch4_orig = df[['Hour', column]].values
    start_time = np_timexch4_orig[:, 0].min()
    end_time = np_timexch4_orig[:, 0].max()

    # Use extrapolation of the day shape to get a better performance on the edges
    if extrapolate:
        np_timexch4 = extrapolation(np_timexch4_orig, cluster_interval, interval)
        index_orig = np.argwhere((np_timexch4[:, 0] >= start_time) & (np_timexch4[:, 0] <= end_time))
    else:
        np_timexch4 = np_timexch4_orig


    # Use moving window for low pass filter calculation (two different versions of low pass filter usage are implemented)
    i = 0  # index for kaiser window
    np_storefitted = np.array([np.zeros(len(np_timexch4))])
    for s in np_timexch4_orig[:, 0]:

        # use full interval by default
        interval_first = interval / 2
        interval_secound = interval / 2
        # check full interval can be used
        if s < start_time + interval / 2:
            # calculate max possible interval
            interval_first = s - start_time
        if s > end_time - interval / 2:
            # calculate max possible interval
            interval_secound = end_time - s + cluster_interval / 2  # '+cluster_interval/2' to keep last measering point

        # get window
        time_w, index = hp.timewindow_middle(np_timexch4[:, 0], s, interval_first, interval_secound)
        # get bigger window when data has been extrapolated
        if extrapolate:
            time_w, index = hp.timewindow_middle(np_timexch4[:, 0], s, interval / 2, interval / 2)

        # get values
        np_inter = np_timexch4[index, 1]

        # check for low pass filter version
        if filter_version == 'butter':
            # use butterworth filter as low pass filter

            np_dummy = np.zeros(len(np_timexch4))
            # to make sure to have engough points for calculation
            if len(np_inter) > (order + 1) * 3:
                y = butter_lowpass_filter(np_inter, cutoff, 1 / cluster_interval, order)
                # shift y such that threshold % data is above filtered curve
                # use quantile with threshold
                y_shift = np.nanquantile(y - np_inter, threshold_quantile)
                if not_shift:
                    y_shift = 0
                y = y - y_shift - offset
                np_dummy[index] = y
                np_storefitted = np.append(np_storefitted, np.array([np_dummy]), axis=0)

        elif filter_version == 'kaiser':
            # use kaiser window as low pass filter
            s = np.round(s, 6)  # avoid numerical errors
            # caluclate masximal possible points per interval
            max_points = int(interval / cluster_interval) + 1

            # getting numpy array with weightings
            np_w = np.kaiser(max_points, level)

            # find to weighting corresponding to measured concentrations
            # optimal Timeseries without gaps
            np_optimalTimeseries = np.arange(s - (interval / 2 - np.round(interval / 2 % cluster_interval, 6)),
                                             s + interval / 2 + cluster_interval / 2,
                                             cluster_interval)  # -cluster_interval/2 is to avoid unexpeceted behavior (e.g. one entry more), - np.round(interval/2 % cluster_interval, 3) is to start at the right point in time such that the timeseries match
            np_optimalTimeseries = np.round(np_optimalTimeseries, 6)  # round is to remove numerical errors

            # measurement Timeseries
            np_measTimeseries = np.round(np_timexch4[index, 0], 6)  # round is to remove numerical errors

            # find value intersection
            np_intersection = np.isin(np_optimalTimeseries, np_measTimeseries)

            # get weighting
            np_weights = np_w[np_intersection]

            # sum of weights must be 1
            np_wightsNorm = 1 / sum(np_weights) * np_weights

            # calulate low pass value for s
            s_value = sum(np_wightsNorm * np_inter)

            np_storefitted[0, i] = s_value
            i = i + 1

    # use data fitting as background version (single calculation, no moving window)
    if filter_version == 'fit_curve':
        # fit a linear and a quadratic function to the concentration series
        # choose by lowest R2 Error which one to use
        def func_lin(x, a, b):
            # linear function to fit
            return a * x + b

        def func_quad(x, a, b, c):
            # quadratic function to fit
            return a * x ** 2 + b * x + c

        x = np_timexch4[:, 0]
        y = np_timexch4[:, 1]

        # curve fitting
        if ((len(x) > 1) & (len(y) > 1)):
            params_lin, params_covariance_lin = curve_fit(func_lin, x, y)
        else:
            pramas_lin = [0, 0]
        if ((len(x) > 2) & (len(y) > 2)):
            params_quad, params_covariance_quad = curve_fit(func_quad, x, y)
        else:
            params_quad = [0, 0, 0]

        # background calculation
        y_lin = func_lin(x, params_lin[0], params_lin[1])
        y_quad = func_quad(x, params_quad[0], params_quad[1], params_quad[2])

        # R2 Error calculation
        r2_lin = r2_score(y, y_lin)
        r2_quad = r2_score(y, y_quad)

        if r2_lin >= r2_quad:
            np_storefitted = np.array([y_lin])
        else:
            np_storefitted = np.array([y_quad])

    # check if an invalide filter version was chosen
    if ((filter_version != 'butter') & (filter_version != 'kaiser') & (filter_version != 'fit_curve')):
        print(
            'ERROR: No valid filter_version is chosen. Please choose for "filter_version" one of ["kaise","butter","fit_curve"]')
        return

    # if extrapolation is used, just keep the origional data interval
    if extrapolate & (filter_version == 'butter'):
        np_storefitted = np_storefitted[:, index_orig].copy()
    elif extrapolate & (filter_version == 'kaiser'):
        np_storefitted = np_storefitted[:, 0:i].copy()
    elif extrapolate & (filter_version == 'fit_curve'):
        np_storefitted = np_storefitted[:, index_orig].copy()

    # shift background under lowest points (already done for filter_version == 'butter')
    if ((filter_version == 'kaiser') | (filter_version == 'fit_curve')):
        y_shift = np.nanquantile(np_storefitted - np_timexch4_orig[:, 1], threshold_quantile)
        if not_shift:
            y_shift = 0
        np_storefitted = np_storefitted - y_shift - offset

    # get mean for every data point
    np.seterr(divide='ignore', invalid='ignore')
    np_fitted = np.true_divide(np_storefitted.sum(0), (np_storefitted != 0).sum(0))

    # return np_fitted
    df[gas + '_fixed_background'] = np_fitted
    return df[['Hour', gas + '_fixed_background']]