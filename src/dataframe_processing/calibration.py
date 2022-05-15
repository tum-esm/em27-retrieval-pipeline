import numpy as np


def apply_calibration(df_data_org, df_cali_org):
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
    df_cali["ID"] = df_cali["ID_SpectrometerCalibration"].apply(lambda x: x[-2:])
    np_siteID = df_data_org["ID_Spectrometer"].unique()
    for site in np_siteID:
        df_cali.loc[df_cali["ID"] == site[:2], "ID"] = site
    # set all unknown enddates to inf
    df_cali.loc[df_cali["EndDate"].isnull(), "EndDate"] = np.inf

    # calibrate data
    df_data = df_data_org.copy()
    for index, row in df_cali.iterrows():
        df_data.loc[
            (df_data["ID_Spectrometer"] == row.ID)
            & (df_data["Date"] >= row.StartDate)
            & (df_data["Date"] < row.EndDate),
            "xch4_ppm",
        ] = (
            df_data.loc[
                (df_data["ID_Spectrometer"] == row.ID)
                & (df_data["Date"] >= row.StartDate)
                & (df_data["Date"] < row.EndDate),
                "xch4_ppm",
            ]
            / row.ch4_calibrationFactor
        )
        df_data.loc[
            (df_data["ID_Spectrometer"] == row.ID)
            & (df_data["Date"] >= row.StartDate)
            & (df_data["Date"] < row.EndDate),
            "xco2_ppm",
        ] = (
            df_data.loc[
                (df_data["ID_Spectrometer"] == row.ID)
                & (df_data["Date"] >= row.StartDate)
                & (df_data["Date"] < row.EndDate),
                "xco2_ppm",
            ]
            / row.co2_calibrationFactor
        )
        df_data.loc[
            (df_data["ID_Spectrometer"] == row.ID)
            & (df_data["Date"] >= row.StartDate)
            & (df_data["Date"] < row.EndDate),
            "xco_ppb",
        ] = (
            df_data.loc[
                (df_data["ID_Spectrometer"] == row.ID)
                & (df_data["Date"] >= row.StartDate)
                & (df_data["Date"] < row.EndDate),
                "xco_ppb",
            ]
            / row.co_calibrationFactor
        )

    return df_data, df_cali
