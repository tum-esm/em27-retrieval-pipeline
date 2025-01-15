"""GeomsGenWriter is a module of PROFFASTpylot.

Generate GEOMS HDF5 files.

License information:
PROFFASTpylot - Running PROFFAST with Python
Copyright (C)   2022    Lena Feld, Benedikt Herkommer,
                        Darko Dubravica,
                        Karlsruhe Institut of Technology (KIT)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3 as published by
the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import h5py
import os
import shutil
import re
import math
import datetime as dt
import numpy as np
import pandas as pd
import glob
from helper import GeomsGenHelper
from prepare import Preparation


class GeomsGenWriter(GeomsGenHelper):
    def __init__(self, geomsgen_inputfile):
        """
        This init can probably be omitted completly once it gets a part
        of the Proffastpylot. for now it is kept for developement.
        """

        # Call the init method of the `Preparation` class.
        # This provides some usefull data within this class.

        super(GeomsGenWriter, self).__init__(geomsgen_inputfile)

        # List of all variables for the GEOMS compliant HDF5 files.
        # For further information, see document "geoms-1.0.pdf":
        # https://avdc.gsfc.nasa.gov/PDF/GEOMS/geoms-1.0.pdf

        self.hdf5_vars = {
            "SRC_PRO": "SOURCE.PRODUCT",
            "DAT_TIM": "DATETIME",
            "ALT": "ALTITUDE",
            "SOL_ZEN": "ANGLE.SOLAR_ZENITH.ASTRONOMICAL",
            "SOL_AZI": "ANGLE.SOLAR_AZIMUTH",
            "INST_LAT": "LATITUDE.INSTRUMENT",
            "INST_LON": "LONGITUDE.INSTRUMENT",
            "INST_ALT": "ALTITUDE.INSTRUMENT",
            "SUR_IND": "SURFACE.PRESSURE_INDEPENDENT",
            "SUR_SRC": "SURFACE.PRESSURE_INDEPENDENT_SOURCE",
            "PRE_IND": "PRESSURE_INDEPENDENT",
            "PRE_SRC": "PRESSURE_INDEPENDENT_SOURCE",
            "TEM_IND": "TEMPERATURE_INDEPENDENT",
            "TEM_SRC": "TEMPERATURE_INDEPENDENT_SOURCE",
            "AIR_COL": "DRY.AIR.COLUMN.PARTIAL_INDEPENDENT",
            "AIR_DEN": "DRY.AIR.NUMBER.DENSITY_INDEPENDENT",
            "AIR_SRC": "DRY.AIR.NUMBER.DENSITY_INDEPENDENT_SOURCE",
            "H2O_COL": "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR",
            "H2O_UNC": (
                "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION." "SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            ),
            "H2O_APR": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI",
            "H2O_SRC": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
            "H2O_AVK": "H2O.COLUMN_ABSORPTION.SOLAR_AVK",
            "CO2_COL": "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR",
            "CO2_UNC": (
                "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION." "SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            ),
            "CO2_APR": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI",
            "CO2_SRC": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
            "CO2_AVK": "CO2.COLUMN_ABSORPTION.SOLAR_AVK",
            "CH4_COL": "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR",
            "CH4_UNC": (
                "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION." "SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            ),
            "CH4_APR": "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI",
            "CH4_SRC": "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
            "CH4_AVK": "CH4.COLUMN_ABSORPTION.SOLAR_AVK",
            "CO_COL": "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR",
            "CO_UNC": (
                "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION." "SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            ),
            "CO_APR": "CO.MIXING.RATIO.VOLUME.DRY_APRIORI",
            "CO_SRC": "CO.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
            "CO_AVK": "CO.COLUMN_ABSORPTION.SOLAR_AVK",
        }

        # List of common attributes for the variables of the GEOMS
        # compliant HDF5 files.
        # This list is not used for the source variables.

        self.hdf5_atts = {
            "VAR_DATA_TYPE": "",
            "VAR_DEPEND": "",
            "VAR_DESCRIPTION": "",
            "VAR_FILL_VALUE": -900000.0,
            "VAR_NAME": "",
            "VAR_NOTES": "",
            "VAR_SIZE": "",
            "VAR_SI_CONVERSION": "",
            "VAR_UNITS": "",
            "VAR_VALID_MAX": 0,
            "VAR_VALID_MIN": 0,
            "_FillValue": -900000.0,
            "units": "",
            "valid_range": [0, 0],
        }

        # List of common attributes for the source variables of
        # the GEOMS compliant HDF5 files.

        self.hdf5_atts_src = {
            "VAR_DATA_TYPE": "",
            "VAR_DEPEND": "",
            "VAR_DESCRIPTION": "",
            "VAR_FILL_VALUE": "",
            "VAR_NAME": "",
            "VAR_NOTES": "",
            "VAR_SIZE": "",
            "VAR_SI_CONVERSION": "",
            "VAR_UNITS": "",
            "VAR_VALID_MAX": "",
            "VAR_VALID_MIN": "",
            "_FillValue": "",
        }

        self.file_name = ""
        self.variables = []

    def generate_GEOMS_at(self, day):
        """Create a HDF5geoms file for a specific day"""

        self.variables = []

        self.logger.debug("Generating a HDF5geoms file for {}.".format(day.strftime("%Y-%m-%d")))

        if not isinstance(day, dt.datetime):
            self.logger.error

        # Create path and preliminary name for the output HDF5 file.

        self.geoms_out = "_".join([self.site_name, self.instrument_number, "GEOMS_OUT.h5"])

        geoms_file = os.path.join(self.geoms_out_path, "GEOMS_OUT.h5")

        # Create GEOMS output file.

        self.MyHDF5 = h5py.File(geoms_file, "w")

        # Get data from the PROFFAST inparms output files

        # df = self.get_data_content(day)
        # PROFFAST output (df pandas data frame)
        self.create_invparms_content(day)  # invparms file
        df = self.df

        # After applying the quality filter for SZA and XAIR
        # (see get_invparms_content),
        # at least 11 (or 12 ???) remaining measurements per measurement day
        # are required to generate an HDF5 file.

        if df is None:
            self.logger.error(
                f"HDF file generation stopped for {day.strftime('%Y-%m-%d')} "
                "while reading invparms file! Less than 11 valid measurement "
                "points."
            )
            self.MyHDF5.close()
            return

        # Get additional information from the colsens, pT_fast_out, and
        # VMR_fast_out PROFFAST output files.

        vmr = self.get_vmr_content(day)  # VMR file
        ptf = self.get_pt_content(day)  # pT file
        sen = self.get_colsens_int(df, day)  # col sens file (including a
        # sza interpolation)

        if (vmr is None) or (ptf is None) or (sen is None):
            self.logger.error(
                "HDF file generation stopped while reading VMR, pT, or " "colsens file!"
            )
            self.MyHDF5.close()
            return

        # Write all variables for generating the GEOMS compliant HDF5 files.

        self.write_source("SRC_PRO")  # "SOURCE.PRODUCT"

        # "DATETIME"
        self.write_datetime(df, "DAT_TIM")
        # "ALTITUDE"
        self.write_altitude(df, ptf, "ALT")
        # "ANGLE.SOLAR_ZENITH.ASTRONOMICAL"
        self.write_solar_angle_zenith(df, "SOL_ZEN")
        # "ANGLE.SOLAR_AZIMUTH"
        self.write_solar_angle_azimuth(df, "SOL_AZI")
        # "LATITUDE.INSTRUMENT"
        self.write_instr_latitude(df, "INST_LAT")
        # "LONGITUDE.INSTRUMENT"
        self.write_instr_longitude(df, "INST_LON")
        # "ALTITUDE.INSTRUMENT"
        self.write_instr_altitude(df, "INST_ALT")
        # "SURFACE.PRESSURE_INDEPENDENT"
        self.write_surface_pressure(df, "SUR_IND")
        # "SURFACE.PRESSURE_INDEPENDENT_SOURCE"
        self.write_surface_pressure_src(df, "SUR_SRC")
        # "PRESSURE_INDEPENDENT"
        self.write_pressure(df, ptf, "PRE_IND")
        # "PRESSURE_INDEPENDENT_SOURCE"
        self.write_pressure_src(df, "PRE_SRC")
        # "TEMPERATURE_INDEPENDENT"
        self.write_temperature(df, ptf, "TEM_IND")
        # "TEMPERATURE_INDEPENDENT_SOURCE"
        self.write_temperature_src(df, "TEM_SRC")

        # "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
        self.write_col(df, "H2O_COL")
        # "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
        self.write_col_unc(df, "H2O_UNC")
        # "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI",
        self.write_apr(df, ptf, vmr, "H2O_APR")
        # "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
        self.write_apr_src(df, "H2O_SRC")
        # "H2O.COLUMN_ABSORPTION.SOLAR_AVK",
        self.write_avk(df, ptf, sen, "H2O_AVK")

        # "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
        self.write_col(df, "CO2_COL")
        # "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
        self.write_col_unc(df, "CO2_UNC")
        # "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI",
        self.write_apr(df, ptf, vmr, "CO2_APR")
        # "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
        self.write_apr_src(df, "CO2_SRC")
        # "CO2.COLUMN_ABSORPTION.SOLAR_AVK",
        self.write_avk(df, ptf, sen, "CO2_AVK")

        # "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
        self.write_col(df, "CH4_COL")
        # "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
        self.write_col_unc(df, "CH4_UNC")
        # "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI",
        self.write_apr(df, ptf, vmr, "CH4_APR")
        # "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
        self.write_apr_src(df, "CH4_SRC")
        # "CH4.COLUMN_ABSORPTION.SOLAR_AVK",
        self.write_avk(df, ptf, sen, "CH4_AVK")

        # "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
        self.write_col(df, "CO_COL")
        # "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
        self.write_col_unc(df, "CO_UNC")
        # "CO.MIXING.RATIO.VOLUME.DRY_APRIORI",
        self.write_apr(df, ptf, vmr, "CO_APR")
        # "CO.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE",
        self.write_apr_src(df, "CO_SRC")
        # "CO.COLUMN_ABSORPTION.SOLAR_AVK",
        self.write_avk(df, ptf, sen, "CO_AVK")

        # "DRY.AIR.COLUMN.PARTIAL_INDEPENDENT"
        self.write_air_partial(df, ptf, "AIR_COL")
        # "DRY.AIR.NUMBER.DENSITY_INDEPENDENT"
        self.write_air_density(df, ptf, "AIR_DEN")
        # "DRY.AIR.NUMBER.DENSITY_INDEPENDENT_SOURCE"
        self.write_air_density_src(df, "AIR_SRC")

        # Write meta information for the variables stored in the HDF5 files.

        self.write_metadata(day, df)
        geoms_file_name = os.path.join(self.geoms_out_path, self.file_name)

        # close file and write to hard disk.

        self.MyHDF5.close()

        # Remove existing file and rename preliminary file name.

        if os.path.exists(geoms_file_name):
            os.remove(geoms_file_name)
            # delete file in case the file already exits
        os.rename(geoms_file, geoms_file_name)
        self.logger.info(
            f"The HDF5geoms file for {day.strftime('%Y-%m-%d')} was written "
            f"to {geoms_file_name}"
        )

    def get_start_stop_date_time(self, day, df):
        # Get date and time of the first and last measurement of the
        # measurement day.

        data = df["JulianDate"]

        # Possible problems with the subsequent quality checks of the HDF5
        # files can be fixed here.

        data = pd.DataFrame(data)
        # data = self._GEOMStoDateTime
        # ((data['JulianDate'] - 2451544.5) * 86400.0)
        data = self._GEOMStoDateTime(np.round((data["JulianDate"] - 2451544.5) * 86400.0))  # ???

        start_date = data[0].strftime("%Y%m%dT%H%M%SZ")
        stop_date = data[-1].strftime("%Y%m%dT%H%M%SZ")
        return (start_date, stop_date)

    def get_start_stop_date_time_csv(self, day):
        """Get start and stop time for each measurement day"""

        df = self.df
        df["UTC"] = pd.to_datetime(df["UTC"])
        # df["LocalTime"] = pd.to_datetime(df["LocalTime"])
        starttime = day.replace(hour=0, minute=0, second=0)
        endtime = day.replace(hour=23, minute=59, second=59)
        datetime_mask = (df["UTC"] > starttime) & (df["UTC"] < endtime)
        # datetime_mask = (df["LocalTime"] > starttime) &
        # (df["LocalTime"]< endtime)

        df = df.loc[datetime_mask]
        data = df["UTC"].to_numpy()
        # data = df["LocalTime"].to_numpy()

        start_date = str(data[0])
        start_date = start_date.replace("-", "")
        start_date = start_date.replace(":", "")
        start_date = start_date.replace(".000000000", "")
        start_date = start_date + "Z"

        stop_date = str(data[-1])
        stop_date = stop_date.replace("-", "")
        stop_date = stop_date.replace(":", "")
        stop_date = stop_date.replace(".000000000", "")
        stop_date = stop_date + "Z"

        return (start_date, stop_date)

    def get_data_content(self, day):
        # Here, the data are obtained from the file that summarizes
        # all the measurement days.
        # The data can be retrieved directly from ivparms.dat file instead.

        df = self.df
        df["UTC"] = pd.to_datetime(df["UTC"])

        # Get the data only for the current day.

        starttime = day.replace(hour=0, minute=0, second=0)
        endtime = day.replace(hour=23, minute=59, second=59)
        datetime_mask = (df["UTC"] > starttime) & (df["UTC"] < endtime)
        df = df.loc[datetime_mask]

        return df

    def get_vmr_content(self, day):
        # The content of the output VMR file is read separately for each
        # measurement day.
        # Each VMR file (i.e. VMR_fast_out.dat) contains:
        # 0: "Index", 1: "Altitude", 2: "H2O", 3: "HDO", 4: "CO2", 5: "CH4",
        # 6: "N2O", 7: "CO", 8: "O2", 9: "HF"
        names = ["Index", "Altitude", "H2O", "HDO", "CO2", "CH4", "N2O", "CO", "O2", "HF"]
        vmr = pd.read_csv(
            self._get_pt_vmr_file(day, "VMR"),
            header=None,
            skipinitialspace=True,
            usecols=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            names=names,
            sep=" ",
            engine="python",
        )

        return vmr

    def get_pt_content(self, day):
        # The content of the pT output file is read separately for
        # each measurement day.
        # Each pT file (i.e. pT_fast_out.dat) contains:
        # 0: "Index", 1: "Altitude", 2: "Temperature", 3: "Pressure",
        # 4: "DryAirColumn", 5: "H2O", 6: "HDO"

        ptf = pd.read_csv(
            self._get_pt_vmr_file(day, "pT"),
            header=0,
            skipinitialspace=True,
            usecols=[0, 1, 2, 3, 4, 5, 6],
            names=["Index", "Altitude", "Tem", "Pre", "DAC", "H2O", "HDO"],
            sep=" ",
            engine="python",
        )

        return ptf

    def create_invparms_content(self, day):
        """Write or overwrite self.df"""

        # !! The following is outdated !!
        # The results of the PROFFAST evaluation are provided in the invparms
        # output file.
        # Each invparms file contains among others the date and time, the
        # pressure and temperature,
        # the coordinates of the EM27/SUN instrument, the solar zenith and
        # azimuth angles,
        # and the trace gas concentrations for CO2, H2O, CH4, and CO.
        # "DateTime": 0, "JulianDate": 0, "HHMMSS_ID": 1,
        # 3: "gndP", 4: "gndT", 5: "latdeg", 6: "londeg", 7: "altim",
        # 8: "appSZA", 9: "azimuth",
        # 10: "XH2O", 12: "XAIR", 14: "XCO2", 17: "XCH4",
        # 20: "XCH4_S5P", 21: "XCO",
        # 25: "H2O", 40: "O2", 67: "CO2", 97: "CH4", 127: "CO", 125: "CH4_S5P",
        # 23: "job01_rms", 63: "job03_rms", 90: "job04_rms", 119: "job05_rms"

        df = self.get_comb_invparms_df(day)
        self.df = df

    def get_colsens_sza(self, day):
        # The column sensivity file (i.e. *colsens.dat") contains the vertical
        # profile of the pressure and
        # the sensitivities for each species (these are H2O, HDO, CO2, CH4,
        # N2O, CO, O2, HF) as function of the SZA.
        # alt [km], p [mbar], SZA [rad]:
        # 0.000E+00, 3.965E-01, 5.607E-01, 6.867E-01, 7.930E-01, 8.866E-01,
        # 9.712E-01, 1.049E+00,
        # 1.121E+00, 1.189E+00, 1.254E+00, 1.315E+00, 1.373E+00, 1.430E+00,
        # 1.484E+00

        sza = []
        alt = []
        pre = []
        sen = []

        # Get path and name for the column sensitivity file of a certain day.

        day_str = day.strftime("%y%m%d")
        colsens_filename = f"{self.site_name}{day_str}-colsens.dat"
        path = os.path.join(self.result_folder, "raw_output_proffast", colsens_filename)

        # Read pressure and sensitivities as function of the altitude and SZA.

        with open(path, "r") as file:
            for i in range(8):  # H2O, HDO, CO2, CH4, N2O, CO, O2, HF
                sza.append([])
                alt.append([])
                pre.append([])
                sen.append([])

                for j in range(6):  # 6 header lines for each species
                    header = file.readline()  # skip header line
                    if j == 3:  # read SZA [rad] values in the third line
                        header = re.sub(" +", "\t", header)
                        header = header.split("\t")  # tab separator
                        sza[i] = np.array(header[3:])  # SZA header/columns
                        sza[i] = sza[i].astype(float)  # string to float

                for j in range(49):  # number of altitude levels
                    line = file.readline()[1:-1]  # skip first empty
                    # space and carriage return character at the end
                    line = re.sub(" +", ",", line)  # replace empty spaces
                    # by a comma
                    line = line.split(",")  # split line into columns

                    alt[i].append(line[0])  # altitude (first column)
                    pre[i].append(line[1])  # pressure (second column)

                    sen[i].append([])
                    for k in range(2, len(line)):  # SZA (third column
                        # upwards, total 15 columns)
                        sen[i][j].append(float(line[k]))

        file.close()

        sza = np.array(sza, dtype=float)  # SZA [deg]
        alt = np.array(alt, dtype=float)  # altitude [km]
        pre = np.array(pre, dtype=float)  # pressure [mbar]
        sen = np.array(sen, dtype=float)  # sensitivity

        return sza, alt, pre, sen

    def get_colsens_int(self, df, day):
        # Here, the interpolation of SZA is calculated to be consistent
        # with the a-priori altitude levels of the map-files.
        # Then, the gas sensitivities are calculated using the
        # interpolated SZA values.

        sza, alt, pre, sen = self.get_colsens_sza(day)

        if (sza is None) or (alt is None) or (pre is None) or (sen is None):
            return None

        appSZA = df["appSZA"].to_numpy()

        gas_sens = []

        for k in range(8):  # H2O, HDO, CO2, CH4, N2O, CO, O2, HF
            gas_sens.append([])

            for i in range(len(appSZA)):
                # number of measurements

                gas_sens[k].append([])

                SZA_app_rad = appSZA[i] * 2.0 * math.pi / 360.0
                # SZA_app_deg = appSZA[i]

                for j in range(len(sza[k]) - 1):  # number SZA angels
                    SZA_sen_rad_1 = sza[k][j]
                    # SZA_sen_deg_1 = sza[k][j] / 2.0 / math.pi * 360.
                    SZA_sen_rad_2 = sza[k][j + 1]
                    # SZA_sen_deg_2 = sza[k][j+1] / 2.0 / math.pi * 360.
                    SZA_dif_rad = SZA_sen_rad_2 - SZA_sen_rad_1
                    # SZA_dif_deg = SZA_sen_deg_2 - SZA_sen_deg_1

                    if SZA_app_rad >= SZA_sen_rad_1 and SZA_app_rad <= SZA_sen_rad_2:
                        for h in range(len(alt[k])):
                            gas_1 = sen[k][h][j]
                            gas_2 = sen[k][h][j + 1]
                            gas_dif = gas_2 - gas_1

                            m_rad = gas_dif / SZA_dif_rad
                            # m_deg = gas_dif/SZA_dif_deg

                            b_gas = gas_1 - m_rad * SZA_sen_rad_1

                            # gas interpolation
                            gas_int = m_rad * SZA_app_rad + b_gas
                            gas_sens[k][i].append(gas_int)

                    elif j == len(sza[k]) - 2 and SZA_app_rad > sza[k][len(sza) - 1]:
                        for h in range(len(alt[k])):
                            gas_1 = sen[k][h][j]
                            gas_2 = sen[k][h][j + 1]
                            gas_dif = gas_2 - gas_1

                            m_rad = gas_dif / SZA_dif_rad
                            # m_deg = gas_dif/SZA_dif_deg

                            b_gas = gas_1 - m_rad * SZA_sen_rad_1

                            # gas extrapolation
                            gas_int = m_rad * SZA_app_rad + b_gas
                            gas_sens[k][i].append(gas_int)
        return gas_sens

    def get_col_unc(self, df):
        # The error calculation (uncertainty) is performed
        # by using the column mixing ratios and dry air mole fraction.

        XH2O = df["XH2O"].to_numpy()
        XCO2 = df["XCO2"].to_numpy()
        XCH4 = df["XCH4"].to_numpy()
        XCO = df["XCO"].to_numpy()

        AvgNr = 11  # number of moving mean values
        ErrNr = int(AvgNr / 2)  # number of moving mean values divided by two
        MeaNr = len(XH2O)  # number of measurements

        # Calculation of the moving mean for each species with 11 data points.

        XH2O_mean = np.zeros(df["JulianDate"].shape)
        XCO2_mean = np.zeros(df["JulianDate"].shape)
        XCH4_mean = np.zeros(df["JulianDate"].shape)
        XCO_mean = np.zeros(df["JulianDate"].shape)

        for i in range(MeaNr - AvgNr + 1):  # moving mean calculation
            XH2O_mean_tmp = 0.0
            XCO2_mean_tmp = 0.0
            XCH4_mean_tmp = 0.0
            XCO_mean_tmp = 0.0

            for j in range(AvgNr):
                XH2O_mean_tmp += XH2O[i + j]
                XCO2_mean_tmp += XCO2[i + j]
                XCH4_mean_tmp += XCH4[i + j]
                XCO_mean_tmp += XCO[i + j]

            XH2O_mean[i + ErrNr] = XH2O_mean_tmp / float(AvgNr)
            XCO2_mean[i + ErrNr] = XCO2_mean_tmp / float(AvgNr)
            XCH4_mean[i + ErrNr] = XCH4_mean_tmp / float(AvgNr)
            XCO_mean[i + ErrNr] = XCO_mean_tmp / float(AvgNr)

        for i in range(ErrNr):  # first entries const
            XH2O_mean[i] = XH2O_mean[ErrNr]
            XCO2_mean[i] = XCO2_mean[ErrNr]
            XCH4_mean[i] = XCH4_mean[ErrNr]
            XCO_mean[i] = XCO_mean[ErrNr]

        for i in range(ErrNr):  # last entries const
            XH2O_mean[MeaNr - i - 1] = XH2O_mean[MeaNr - ErrNr - 1]
            XCO2_mean[MeaNr - i - 1] = XCO2_mean[MeaNr - ErrNr - 1]
            XCH4_mean[MeaNr - i - 1] = XCH4_mean[MeaNr - ErrNr - 1]
            XCO_mean[MeaNr - i - 1] = XCO_mean[MeaNr - ErrNr - 1]

        # The error calculation is based on the difference between
        # the column mixing ratios
        # and the the moving mean value for each trace gas.
        # Therefore, it corresponds to a standard deviation with respect to
        # the moving mean.

        XH2O_err = np.zeros(MeaNr)
        XCO2_err = np.zeros(MeaNr)
        XCH4_err = np.zeros(MeaNr)
        XCO_err = np.zeros(MeaNr)

        for i in range(MeaNr - AvgNr + 1):
            XH2O_err_tmp = 0.0
            XCO2_err_tmp = 0.0
            XCH4_err_tmp = 0.0
            XCO_err_tmp = 0.0

            for j in range(AvgNr):
                XH2O_err_tmp += np.power(XH2O[i + j] - XH2O_mean[i + j], 2)
                XCO2_err_tmp += np.power(XCO2[i + j] - XCO2_mean[i + j], 2)
                XCH4_err_tmp += np.power(XCH4[i + j] - XCH4_mean[i + j], 2)
                XCO_err_tmp += np.power(XCO[i + j] - XCO_mean[i + j], 2)

            XH2O_err[i + ErrNr] = np.sqrt(XH2O_err_tmp / float(AvgNr - 1))
            XCO2_err[i + ErrNr] = np.sqrt(XCO2_err_tmp / float(AvgNr - 1))
            XCH4_err[i + ErrNr] = np.sqrt(XCH4_err_tmp / float(AvgNr - 1))
            XCO_err[i + ErrNr] = np.sqrt(XCO_err_tmp / float(AvgNr - 1)) * 1000.0

            if XH2O[i + ErrNr] == -900000.0:
                XH2O_err[i + ErrNr] = -900000.0
            if XCO2[i + ErrNr] == -900000.0:
                XCO2_err[i + ErrNr] = -900000.0
            if XCH4[i + ErrNr] == -900000.0:
                XCH4_err[i + ErrNr] = -900000.0
            if XCO[i + ErrNr] == -900000.0:
                XCO_err[i + ErrNr] = -900000.0

        # The uncertainty for the first and last entries is constant.

        for i in range(ErrNr):
            XH2O_err[i] = XH2O_err[ErrNr]
            XCO2_err[i] = XCO2_err[ErrNr]
            XCH4_err[i] = XCH4_err[ErrNr]
            XCO_err[i] = XCO_err[ErrNr]

            if XH2O[i] == -900000.0:
                XH2O_err[i] = -900000.0
            if XCO2[i] == -900000.0:
                XCO2_err[i] = -900000.0
            if XCH4[i] == -900000.0:
                XCH4_err[i] = -900000.0
            if XCO[i] == -900000.0:
                XCO_err[i] = -900000.0

        for i in range(ErrNr):
            XH2O_err[MeaNr - i - 1] = XH2O_err[MeaNr - ErrNr - 1]
            XCO2_err[MeaNr - i - 1] = XCO2_err[MeaNr - ErrNr - 1]
            XCH4_err[MeaNr - i - 1] = XCH4_err[MeaNr - ErrNr - 1]
            XCO_err[MeaNr - i - 1] = XCO_err[MeaNr - ErrNr - 1]

            if XH2O[MeaNr - i - 1] == -900000.0:
                XH2O_err[MeaNr - i - 1] = -900000.0
            if XCO2[MeaNr - i - 1] == -900000.0:
                XCO2_err[MeaNr - i - 1] = -900000.0
            if XCH4[MeaNr - i - 1] == -900000.0:
                XCH4_err[MeaNr - i - 1] = -900000.0
            if XCO[MeaNr - i - 1] == -900000.0:
                XCO_err[MeaNr - i - 1] = -900000.0

        return XH2O_err, XCO2_err, XCH4_err, XCO_err

    def write_source(self, cont):
        # "SRC_PRO": "SOURCE.PRODUCT"

        # Write information to the HDF5 file which is relevant to the
        # source history.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = "Some Information."

        self.hdf5_atts_src["VAR_DATA_TYPE"] = "STRING"
        self.hdf5_atts_src["VAR_DEPEND"] = "INDEPENDENT"
        self.hdf5_atts_src["VAR_DESCRIPTION"] = (
            "Information relevant to the source history "
            "of the Metadata and Data in the form "
            "Original_Archive;Original_Filename;"
            "Original_File_Generation_Date"
        )
        self.hdf5_atts_src["VAR_NAME"] = dataset_name
        # self.hdf5_atts_src["VAR_NOTES"] = ""
        self.hdf5_atts_src["VAR_SIZE"] = "1"

        self.SRC_dtst = self._write_dataset_src(data, dataset_name, self.hdf5_atts_src)

    def write_datetime(self, df, cont):
        # "DAT_TIM": "DATETIME"

        # Write DateTime to the HDF5 file
        # (MJD2K is 0.0 on January 1, 2000 at 00:00:00 UTC).

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        datetime_notes = self.input_args["DATETIME_NOTES"]

        data = df["JulianDate"].to_numpy()

        data = self._GEOMStoDateTime((data - 2451544.5) * 86400.0)
        # data = self._GEOMStoDateTime(np.round((data - 2451544.5) * 86400.0))
        # ???
        data = self._DateTimeToGEOMS(data) / 86400.0

        self.hdf5_atts["VAR_DATA_TYPE"] = "DOUBLE"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = "MJD2K is 0.0 on January 1, 2000 at 00:00:00 UTC"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        self.hdf5_atts["VAR_NOTES"] = datetime_notes
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;86400.0;s"
        self.hdf5_atts["VAR_UNITS"] = "MJD2K"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "MJD2K"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset_dt(data, dataset_name, self.hdf5_atts)

    def write_altitude(self, df, ptf, cont):
        # "ALT": "ALTITUDE"

        # Write altitude information used in the a-priori profile matrix.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Altitude"][j] / 1000.0  # in km

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME;ALTITUDE"
        self.hdf5_atts["VAR_DESCRIPTION"] = (
            "A-priori altitude profile matrix. Values " "are monotonically increasing"
        )
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        # self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SIZE"] = str(np.array(";".join(map(str, list(data.shape)))))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E3;m"
        self.hdf5_atts["VAR_UNITS"] = "km"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "km"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_solar_angle_zenith(self, df, cont):
        # "SOL_ZEN": "ANGLE.SOLAR_ZENITH.ASTRONOMICAL"

        # Write solar zenith angle to the HDF5 file
        # (solar astronomical zenith angle).

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = df["appSZA"].to_numpy()

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = (
            "The solar astronomical zenith angle at which " "the measurement was taken"
        )
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.74533E-2;rad"
        self.hdf5_atts["VAR_UNITS"] = "deg"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "deg"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_solar_angle_azimuth(self, df, cont):
        # "SOL_AZI": "ANGLE.SOLAR_AZIMUTH"

        # Write solar azimuth angle to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = df["azimuth"].to_numpy() + 180.0

        # To avoid values lower than 0.0° or higher than 360.0°
        # causing an error message
        # in the quality checks of the HDF5 files, a small numer is
        # added or subtracted.

        for i in range(len(data)):
            if data[i] <= 0.0 + 1.0e-5 or data[i] >= 360.0 - 1.0e-5:
                data[i] = 0.0 + 1.0e-5

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = (
            "The azimuth viewing direction of the instrument "
            "using north as the reference plane and increasing "
            "clockwise (0 for north 90 for east and so on)"
        )
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.74533E-2;rad"
        self.hdf5_atts["VAR_UNITS"] = "deg"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "deg"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_instr_latitude(self, df, cont):
        # "INST_LAT": "LATITUDE.INSTRUMENT"

        # Write the instrument's latitude to the HDF5 file
        # (i.e. the geolocation with + for north and - for south).

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = df["latdeg"].to_numpy()

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Instrument geolocation (+ for north; - for south)"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.74533E-2;rad"
        self.hdf5_atts["VAR_UNITS"] = "deg"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "deg"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_instr_longitude(self, df, cont):
        # "INST_LON": "LONGITUDE.INSTRUMENT"

        # Write the instrument's longitude to the HDF5 file
        # (i.e. the geolocation with + for east and - for west).

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = df["londeg"].to_numpy()

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Instrument geolocation (+ for east; - for west)"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.74533E-2;rad"
        self.hdf5_atts["VAR_UNITS"] = "deg"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "deg"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_instr_altitude(self, df, cont):
        # "INST_ALT": "ALTITUDE.INSTRUMENT"

        # Write the instrument's altitude to the HDF5 file
        # (i.e. the geolocation).

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = df["altim"].to_numpy()

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Instrument geolocation"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E3;m"
        self.hdf5_atts["VAR_UNITS"] = "km"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "km"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_surface_pressure(self, df, cont):
        # "SUR_IND": "SURFACE.PRESSURE_INDEPENDENT"

        #  Write the surface pressure (i.e. the ground pressure)
        # to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = df["gndP"].to_numpy()

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Surface/ground pressure"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E2;kg m-1 s-2"
        self.hdf5_atts["VAR_UNITS"] = "hPa"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "hPa"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_surface_pressure_src(self, df, cont):
        # "SUR_SRC": "SURFACE.PRESSURE_INDEPENDENT_SOURCE"

        # Write the source of the surface pressure
        # (i.e. the ground pressure) to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = df["londeg"].to_numpy()
        data_size = data.size
        data_src = [f"{self.input_args['PRESSURE_SOURCE']}"] * data_size

        self.hdf5_atts_src["VAR_DATA_TYPE"] = "STRING"
        self.hdf5_atts_src["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts_src["VAR_DESCRIPTION"] = (
            "Surface pressure profile source (e.g. Mercury barometer etc.)"
        )
        self.hdf5_atts_src["VAR_NAME"] = dataset_name
        # self.hdf5_atts_src["VAR_NOTES"] = ""
        self.hdf5_atts_src["VAR_SIZE"] = str(np.size(data))

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, self.hdf5_atts_src)

    def write_pressure(self, df, ptf, cont):
        # "PRE_IND": "PRESSURE_INDEPENDENT"

        # Write the effective air pressure at each
        # altitude level to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Pre"][j] / 100.0  # hPa

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME;ALTITUDE"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Effective air pressure at each altitude"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        # self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SIZE"] = str(np.array(";".join(map(str, list(data.shape)))))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E2;kg m-1 s-2"
        self.hdf5_atts["VAR_UNITS"] = "hPa"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "hPa"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_pressure_src(self, df, cont):
        # "PRE_SRC": "PRESSURE_INDEPENDENT_SOURCE"

        # Write the source of the effective air pressure
        # for each altitude to the HDf5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data_src = []

        for i in range(df["JulianDate"].shape[0]):
            data_src.append("Pressure profile from NCEP at local noon")

        self.hdf5_atts_src["VAR_DATA_TYPE"] = "STRING"
        self.hdf5_atts_src["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts_src["VAR_DESCRIPTION"] = "Pressure profile source (hydrostatic)"
        self.hdf5_atts_src["VAR_NAME"] = dataset_name
        # self.hdf5_atts_src["VAR_NOTES"] = ""
        self.hdf5_atts_src["VAR_SIZE"] = str(np.size(data_src))

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, self.hdf5_atts_src)

    def write_temperature(self, df, ptf, cont):
        # "TEM_IND": "TEMPERATURE_INDEPENDENT"

        # Write the effective air temperature at each
        # altitude to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = ptf["Tem"][j]

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME;ALTITUDE"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Effective air temperature at each altitude"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        # self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SIZE"] = str(np.array(";".join(map(str, list(data.shape)))))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0;K"
        self.hdf5_atts["VAR_UNITS"] = "K"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "K"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_temperature_src(self, df, cont):
        # "TEM_SRC": "TEMPERATURE_INDEPENDENT_SOURCE"

        # Write the source of the effective air pressure for
        # each altitude to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data_src = []

        for i in range(df["JulianDate"].shape[0]):
            data_src.append("Temperature profile from NCEP at local noon")

        self.hdf5_atts_src["VAR_DATA_TYPE"] = "STRING"
        self.hdf5_atts_src["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts_src["VAR_DESCRIPTION"] = (
            "Temperature profile source (e.g. Lidar NCEP Sonde ECMWF etc.)"
        )
        self.hdf5_atts_src["VAR_NAME"] = dataset_name
        # self.hdf5_atts_src["VAR_NOTES"] = ""
        self.hdf5_atts_src["VAR_SIZE"] = str(np.size(data_src))

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, self.hdf5_atts_src)

    def write_col(self, df, cont):
        # "XXX_COL": "XXX.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"

        # Write column average dry air mole fractions for
        # each trace gas to HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        # Convert data to numpy array.
        if cont == "H2O_COL":
            # "H2O_COL": "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XH2O"].to_numpy()
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CO2_COL":
            # "CO2_COL": "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XCO2"].to_numpy()
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CH4_COL":
            # "CH4_COL": "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XCH4"].to_numpy()
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CO_COL":
            # "CO_COL":  "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR"
            data = df["XCO"].to_numpy() * 1000.0  # in ppbv
            data[data < 0] = -900000.0  # default fill value
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-9;1"
            self.hdf5_atts["VAR_UNITS"] = "ppbv"
            self.hdf5_atts["units"] = "ppbv"

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Column average dry air mole fraction"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        # self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_col_unc(self, df, cont):
        # "XXX_UNC":
        # "XXX.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"

        # Write uncertainty on the retrieved total column
        # for each trace gas to HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape)

        h2o_unc, co2_unc, ch4_unc, co_unc = self.get_col_unc(df)

        if cont == "H2O_UNC":
            # "H2O_UNC":
            # "H2O.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = h2o_unc  # uncertainty for H2O
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CO2_UNC":
            # "CO2_UNC":
            # "CO2.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = co2_unc  # uncertainty for CO2
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CH4_UNC":
            # "CH4_UNC":
            # "CH4.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = ch4_unc  # uncertainty for CH4
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CO_UNC":
            # "CO_UNC":
            # "CO.COLUMN.MIXING.RATIO.VOLUME.DRY_ABSORPTION.SOLAR_UNCERTAINTY.RANDOM.STANDARD"
            data = co_unc  # uncertainty for CO
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-9;1"
            self.hdf5_atts["VAR_UNITS"] = "ppbv"
            self.hdf5_atts["units"] = "ppbv"

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts["VAR_DESCRIPTION"] = np.bytes_(
            "Total random uncertainty on the retrieved total column "
            "(expressed in same units as the column)"
        )
        # "Total random uncertainty on the retrieved total column \
        # (expressed in same units as the column)"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        # self.hdf5_atts["VAR_SIZE"] = \
        # str(np.array(';'.join(map(str,list(data.shape)))))
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_apr(self, df, ptf, vmr, cont):
        """Write prior total vertical column for each trace gas to the HDF5 file.
        "XXX_APR": "XXX.MIXING.RATIO.VOLUME.DRY_APRIORI"""
        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        if cont == "H2O_APR":
            # "H2O_APR": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI"
            H2O_prior = ptf["H2O"]  # VMR prior for H2O
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = H2O_prior[j]  # in ppm
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CO2_APR":
            # "CO2_APR": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI"
            CO2_prior = vmr["CO2"]  # VMR prior for CO2
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CO2_prior[j]  # in ppm
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-6;1"
            self.hdf5_atts["VAR_UNITS"] = "ppmv"
            self.hdf5_atts["units"] = "ppmv"
        elif cont == "CH4_APR":
            # "CH4_APR": "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI"
            CH4_prior = vmr["CH4"] * 1000.0  # VMR prior for CH4
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CH4_prior[j]  # in ppb
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-9;1"
            self.hdf5_atts["VAR_UNITS"] = "ppbv"
            self.hdf5_atts["units"] = "ppbv"
        elif cont == "CO_APR":
            # "CO_APR": "CO.MIXING.RATIO.VOLUME.DRY_APRIORI"
            CO_prior = vmr["CO"] * 1000.0  # VMR prior for CO
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = CO_prior[j]  # in ppb
            self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0E-9;1"
            self.hdf5_atts["VAR_UNITS"] = "ppbv"
            self.hdf5_atts["units"] = "ppbv"

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME;ALTITUDE"
        self.hdf5_atts["VAR_DESCRIPTION"] = "A-priori total vertical column of target gas"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        # self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SIZE"] = str(np.array(";".join(map(str, list(data.shape)))))
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_apr_src(self, df, cont):
        # "XXX_SRC": "XXX.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"

        # Write source of the a-prior total vertical column for each
        # trace gas to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data_src = []
        ggg_ver = self.input_args["APRIORI_SOURCE"]

        for i in range(df["JulianDate"].shape[0]):
            if cont == "H2O_SRC":
                # "H2O_SRC": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Total vertical column of H2O from NCEP at local noon")
            elif cont == "CO2_SRC":
                # "CO2_SRC": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Map file GFIT Code ({})".format(ggg_ver))
            elif cont == "CH4_SRC":
                # "CH4_SRC": "CH4.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Map file GFIT Code ({})".format(ggg_ver))
            elif cont == "CO_SRC":
                # "CO_SRC":  "CO.MIXING.RATIO.VOLUME.DRY_APRIORI.SOURCE"
                data_src.append("Map file GFIT Code ({})".format(ggg_ver))

        self.hdf5_atts_src["VAR_DATA_TYPE"] = "STRING"
        self.hdf5_atts_src["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts_src["VAR_DESCRIPTION"] = (
            "Source of the vertical profile of a-priori per layer"
        )
        self.hdf5_atts_src["VAR_NAME"] = dataset_name
        # self.hdf5_atts_src["VAR_NOTES"] = ""
        self.hdf5_atts_src["VAR_SIZE"] = str(np.size(data_src))

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, self.hdf5_atts_src)

    def write_avk(self, df, ptf, sen, cont):
        # "XXX_AVK": "XXX.COLUMN_ABSORPTION.SOLAR_AVK"

        # Write column sensitivities assosiated with the total vertical column
        # for each trace gas to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        if cont == "H2O_AVK":
            # "H2O_APR": "H2O.MIXING.RATIO.VOLUME.DRY_APRIORI"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[0][i][j]  # 0: "CO2_int"
        elif cont == "CO2_AVK":
            # "CO2_APR": "CO2.MIXING.RATIO.VOLUME.DRY_APRIORI"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[2][i][j]  # 1: "CH4_int"
        elif cont == "CH4_AVK":
            # "CH4_APR": "CH4.MIXING.RATIO.VOLUME.DRY_APRIOR"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[3][i][j]  # 2: "CO_int"
        elif cont == "CO_AVK":
            # "CO_APR": "CO.MIXING.RATIO.VOLUME.DRY_APRIORI"
            for i in range(df["JulianDate"].shape[0]):
                for j in range(ptf["Altitude"].shape[0]):
                    data[i][j] = sen[5][i][j]  # 3: "H2O_int"

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME;ALTITUDE"
        self.hdf5_atts["VAR_DESCRIPTION"] = (
            "Column sensitivity associated with the total vertical column " "of the target gas"
        )
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        # self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SIZE"] = str(np.array(";".join(map(str, list(data.shape)))))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.0;1"
        self.hdf5_atts["VAR_UNITS"] = "1"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "1"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_air_partial(self, df, ptf, cont):
        # "AIR_COL": "DRY.AIR.COLUMN.PARTIAL_INDEPENDENT"

        # Write vertical profile of partial columns of air number densities
        # (for conversion between VMR and partial column profile).
        # 0: "Index", 1: "Altitude", 2: "Tem", 3: "Pre", 4: "DAC",
        # 5: "H2O", 6: "HDO"
        # 0: "Index", 1: "Altitude", 2: "Temperature", 3: "Pressure",
        # 4: "Column", 5: "H2O", 6: "HDO"

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        k_B = 1.3807e-23  # 1.380649E-23 # k_boltz = 1.3807e-23

        T_prior = ptf["Tem"]
        P_prior = ptf["Pre"] / 100.0  # conversion Pa to hPa
        H2O_prior = ptf["H2O"]  # / 10000.0 ???

        p_dry = P_prior * 1.0 / (1.0 + 1.0e-6 * H2O_prior)
        # / 100.0 for conversion Pa to hPa
        n_dry = p_dry / (k_B * T_prior)

        # Calcualtion of the vertical profile, i.e. the partial
        # columns of air number densities.
        # Each layer is obtained by an integration between two boundary layers.

        for i in range(df["JulianDate"].shape[0]):
            sum1 = 0.0
            sum2 = 0.0

            for j in range(ptf["Altitude"].shape[0]):
                if j < len(ptf["Altitude"]) - 1:
                    h1 = float(ptf["Altitude"][j])
                    # * 1000.0 for conversion km to m
                    h2 = float(ptf["Altitude"][j + 1])
                    # * 1000.0 for conversion km to m

                    n1_dry = float(n_dry[j])
                    n2_dry = float(n_dry[j + 1])
                    sc_dry = (h2 - h1) / math.log(n1_dry / n2_dry)
                    n0_dry = n1_dry * math.exp(h1 / sc_dry)

                    Col1 = n0_dry * sc_dry * math.exp(-(h1 / sc_dry))
                    Col2 = n0_dry * sc_dry * math.exp(-(h2 / sc_dry))

                    data[i][j] = 100.0 * (Col1 - Col2)
                    # data[i][H_len-j] = 100.0 * (Col1 - Col2)

                    sum1 += data[i][j]
                    # sum1 += data[i][H_len-j]
                    sum2 += float(ptf["DAC"][j])

                else:
                    data[i][j] = 0
                    # data[i][H_len-j] = 0
                    sum1 += data[i][j]
                    # sum1 += data[i][H_len-j]
                    sum2 += float(ptf["DAC"][j])

        data = data / 1.0e25

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME;ALTITUDE"
        self.hdf5_atts["VAR_DESCRIPTION"] = (
            "Vertical profile of partial columns of air number densities "
            "(for conversion between VMR and partial column profile)"
        )
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        # self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SIZE"] = str(np.array(";".join(map(str, list(data.shape)))))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.66054E1;mol m-2"
        self.hdf5_atts["VAR_UNITS"] = "Zmolec cm-2"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "Zmolec cm-2"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_air_density(self, df, ptf, cont):
        # "AIR_DEN": "DRY.AIR.NUMBER.DENSITY_INDEPENDENT"

        # Write the dry air number density profile to the HDF5 file.
        # 0: "Index", 1: "Altitude", 2: "Tem", 3: "Pre", 4: "DAC", 5:
        # "H2O", 6: "HDO"
        # 0: "Index", 1: "Altitude", 2: "Temperature", 3: "Pressure",
        # 4: "Column", 5: "H2O", 6: "HDO"

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data = np.zeros(df["JulianDate"].shape + ptf["Altitude"].shape)

        k_B = 1.3807e-23  # 1.380649E-23 # k_boltz = 1.3807e-23

        T_prior = ptf["Tem"]
        P_prior = ptf["Pre"] / 100.0  # conversion to hPa
        H2O_prior = ptf["H2O"]  # / 10000.0 ???

        # Calculation of the dry air number density profile.

        p_dry = P_prior * 1.0 / (1.0 + 1.0e-6 * H2O_prior)
        # / 100.0 for conversion Pa to hPa
        n_dry = p_dry / (k_B * T_prior)

        for i in range(df["JulianDate"].shape[0]):
            for j in range(ptf["Altitude"].shape[0]):
                data[i][j] = n_dry[j]

        self.hdf5_atts["VAR_DATA_TYPE"] = "REAL"
        self.hdf5_atts["VAR_DEPEND"] = "DATETIME;ALTITUDE"
        self.hdf5_atts["VAR_DESCRIPTION"] = "Dry air number density profile"
        self.hdf5_atts["VAR_FILL_VALUE"] = -900000.0
        self.hdf5_atts["VAR_NAME"] = dataset_name
        # self.hdf5_atts["VAR_NOTES"] = ""
        # self.hdf5_atts["VAR_SIZE"] = str(np.size(data))
        self.hdf5_atts["VAR_SIZE"] = str(np.array(";".join(map(str, list(data.shape)))))
        self.hdf5_atts["VAR_SI_CONVERSION"] = "0.0;1.66054E-18;mol m-3"
        self.hdf5_atts["VAR_UNITS"] = "molec cm-3"
        self.hdf5_atts["VAR_VALID_MAX"] = np.amax(data)
        self.hdf5_atts["VAR_VALID_MIN"] = np.amin(data)
        self.hdf5_atts["_FillValue"] = -900000.0
        self.hdf5_atts["units"] = "molec cm-3"
        self.hdf5_atts["valid_range"] = [np.amin(data), np.amax(data)]

        self.SRC_dtst = self._write_dataset(data, dataset_name, self.hdf5_atts)

    def write_air_density_src(self, df, cont):
        # "AIR_SRC": "DRY.AIR.NUMBER.DENSITY_INDEPENDENT_SOURCE"

        # Write source of the dry air number density profile
        # (hydrostatic) to the HDF5 file.

        dataset_name = self.hdf5_vars[cont]
        self.variables.append(dataset_name)

        data_src = []

        for i in range(df["JulianDate"].shape[0]):
            data_src.append("Dry air number density profile from NCEP at local noon")

        self.hdf5_atts_src["VAR_DATA_TYPE"] = "STRING"
        self.hdf5_atts_src["VAR_DEPEND"] = "DATETIME"
        self.hdf5_atts_src["VAR_DESCRIPTION"] = (
            "Dry air number density profile source (hydrostatic)"
        )
        self.hdf5_atts_src["VAR_NAME"] = dataset_name
        # self.hdf5_atts_src["VAR_NOTES"] = ""
        self.hdf5_atts_src["VAR_SIZE"] = str(np.size(data_src))

        self.SRC_dtst = self._write_dataset_src(data_src, dataset_name, self.hdf5_atts_src)

    def _get_ils_form_preprocess_inp(self, day):
        """Return ILS from preprocess input file."""
        yymmdd_str = day.strftime("%y%m%d")
        search_path = os.path.join(
            self.result_folder, "input_files", f"preprocess*{yymmdd_str}.inp"
        )
        file_list = glob.glob(search_path)
        if len(file_list) == 0:
            return  # no parameters from ils present
        else:
            preprocess_input_file = file_list[0]

        with open(preprocess_input_file, "r") as f:
            lines = f.readlines()

        # go to second $ (counter i)
        # and read the following two lines (counter j)
        i = 0
        j = 0
        ils = []
        for line in lines:
            if line.startswith("$"):
                i += 1
                continue
            if i == 2:
                if j >= 2:
                    break  # read only 2 lines
                tmp_ils = np.array(line.split(" ")).astype(float)
                ils.extend(tmp_ils)
                j += 1
        return tuple(ils)

    def get_ils_parameters(self, day):
        """Return ILS Parameters if possible.

        ILS parameters are obtained in the following way:
        1. if present the values are taken from the generated prf output
            (since v1.4)
        2. else, the values are taken from the preprocess input file
        3. else, the values can be taken from a given ils-list
            (e.g. from the default list shiped with proffastpylot) if the list
            is given in the geoms input file.

        If the values can be obtained from 1. or 2. and additionally from 3.
        a cross-check is preformed.

        Params:
            day: day to be processed

        Returns:
            tuple (ME1, PE1, ME2, PE2)
        """
        ils_from_prf = None
        # TODO: implent function in run_invers to read ils from .bin files
        ils_from_prep = self._get_ils_form_preprocess_inp(day)
        if self.ils_file is not None:
            try:
                ils_from_file = Preparation.get_ils_from_file(self, day)
            except KeyError:
                self.ils_not_in_file_warning = True
                ils_from_file = None
        else:
            ils_from_file = None

        ils = None
        if ils_from_prep is not None:  # second best ils source (2.)
            ils = ils_from_prep
        if ils_from_prf is not None:  # preferred ils source (1.)
            ils = ils_from_prf

        # compare ils with ils from file
        if ils is not None and ils_from_file is not None:
            if ils != ils_from_file:
                self.logger.error(
                    "Discrepancies in ILS! The ILS read from the ils_list "
                    f"{self.ils_file} {ils_from_file} does not match the "
                    f"ils read from the proffast output {ils}."
                )
            else:
                self.logger.debug("ILS from file and input file agree")

        if ils is None:
            ils = ils_from_file

        return ils

    def write_metadata(self, day, df):
        """Write metadata to the GEOMS file!"""

        # Attribut list, which contains the variables given in the input files.
        attribute_list = [
            "DATA_FILE_VERSION",
            "DATA_LOCATION",
            "DATA_PROCESSOR",
            "DATA_QUALITY",
            "DATA_SOURCE",
            "DATA_TEMPLATE",
            "FILE_DOI",
            "FILE_META_VERSION",
            "PI_NAME",
            "PI_EMAIL",
            "PI_AFFILIATION",
            "PI_ADDRESS",
            "DO_NAME",
            "DO_EMAIL",
            "DO_AFFILIATION",
            "DO_ADDRESS",
            "DS_NAME",
            "DS_EMAIL",
            "DS_AFFILIATION",
            "DS_ADDRESS",
        ]

        for attr in attribute_list:
            # H5Py needs to store the strings using this numpy method:
            # see: https://docs.h5py.org/en/2.4/strings.html
            # Furhtermore they have to be in edged brackets to provide
            # an array.
            self.MyHDF5.attrs[attr] = np.bytes_(self.input_args[attr])

        self.MyHDF5.attrs["DATA_DESCRIPTION"] = np.bytes_(
            f"EM27/SUN ({self.instrument_number}) measurements"
            f" from {self.input_args['SITE_DESCRIPTION']}."
        )

        self.MyHDF5.attrs["DATA_DISCIPLINE"] = np.bytes_(
            "ATMOSPHERIC.CHEMISTRY;REMOTE.SENSING;GROUNDBASED"
        )

        self.MyHDF5.attrs["DATA_GROUP"] = np.bytes_("EXPERIMENTAL;PROFILE.STATIONARY")

        ils = self.get_ils_parameters(day)
        if ils is None:
            ils = "(?, ?, ?, ?)"
            self.ils_filelist_warning = True

        # Get the correction factors from the Calibration_Parameters.csv file.
        corr_fac = self._get_correction_factors()

        self.MyHDF5.attrs["DATA_MODIFICATIONS"] = np.bytes_(
            "ILS parms applied: "
            f"{str(ils)} (ME1, PE1, ME2, PE2). "
            "Calibration factors applied: "
            f"{corr_fac['XCO2_cal']} for XCO2, "
            f"{corr_fac['XCH4_cal']} for XCH4, "
            f"{corr_fac['XH2O_cal']} for XH2O, "
            f"{corr_fac['XCO_cal']} for XCO."
        )

        # Get the start and stop datetime, that is also needed
        # for the file name.

        start, stop = self.get_start_stop_date_time(day, df)
        self.MyHDF5.attrs["DATA_START_DATE"] = np.bytes_(start)
        self.MyHDF5.attrs["DATA_STOP_DATE"] = np.bytes_(stop)

        self.MyHDF5.attrs["DATA_VARIABLES"] = np.bytes_(";".join(self.variables))

        self.MyHDF5.attrs["FILE_ACCESS"] = np.bytes_("COCCON")

        self.MyHDF5.attrs["FILE_GENERATION_DATE"] = np.bytes_(
            dt.datetime.now().strftime("%Y%m%dT%H%M%SZ")
        )

        # Create the final file name of the GEOMS compliant HDF5 file.
        self.file_name = (
            "groundbased_"
            f"{self.input_args['DATA_SOURCE']}_"
            f"{self.input_args['DATA_LOCATION']}_"
            f"{start}_{stop}_"
            f"{self.input_args['DATA_FILE_VERSION']}"
            f".h5"
        ).lower()

        self.MyHDF5.attrs["FILE_NAME"] = np.bytes_(self.file_name)

        self.MyHDF5.attrs["FILE_PROJECT_ID"] = np.bytes_("COCCON")

    def generate_geoms_files(self):
        datetimes = self.get_datetimes()
        geoms_start_date = self.get_start_date()
        geoms_end_date = self.get_end_date()

        self.logger.info(
            f"Generating HDF5geoms files between {self.geoms_start_date} "
            f"and {self.geoms_end_date}."
        )

        for date in datetimes:
            if date < geoms_start_date:
                continue
            elif date > geoms_end_date:
                break
            else:
                self.generate_GEOMS_at(day=date)

        # run information
        if self.ils_not_in_file_warning is True:
            self.logger.warning(
                "The ILS could not be determined and no values are "
                "written to the geoms metadata."
            )
        elif self.ils_filelist_warning is True:
            self.logger.warning(
                f"The ILS was read from the ILS file {self.ils_file}. "
                "Check if this is consistent to the ILS parameters in the "
                "header of the .BIN files!"
            )
        if self.n_removed_values > 0:
            self.logger.info(
                f"The quality filter rejected {self.n_removed_values} values "
                "during the processed period."
            )
