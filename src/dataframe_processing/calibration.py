import pandas as pd
import numpy as np

from src import utils


def apply_calibration(df_data: pd.DataFrame, df_calibration_factors: pd.DataFrame):
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

    assert utils.functions.is_subset_of(
        ["ID_Spectrometer", "Date", "xch4_ppm", "xco2_ppm", "xco_ppb"],
        df_data.columns,
    )
    assert utils.functions.is_subset_of(
        ["ID_SpectrometerCalibration", "EndDate", "StartDate"],
        df_calibration_factors.columns,
    )

    df_calibration_factors["ID"] = df_calibration_factors[
        "ID_SpectrometerCalibration"
    ].apply(lambda x: x[-2:])
    for site in df_data["ID_Spectrometer"].unique():
        df_calibration_factors.loc[
            df_calibration_factors["ID"] == site[:2], "ID"
        ] = site

    # set all unknown enddates to inf
    df_calibration_factors.loc[
        df_calibration_factors["EndDate"].isnull(), "EndDate"
    ] = np.inf

    # calibrate data
    for _, row in df_calibration_factors.iterrows():
        _row_query = (
            (df_data["ID_Spectrometer"] == row["ID"])
            & (df_data["Date"] >= row["StartDate"])
            & (df_data["Date"] < row["EndDate"])
        )
        for gas in ["co", "co2", "ch4"]:
            column_name = f"x{gas}_{utils.constants.UNITS[gas]}"
            df_data.loc[_row_query, column_name] /= row[f"{gas}_calibrationFactor"]

    return df_data, df_calibration_factors
