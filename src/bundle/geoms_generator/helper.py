"""GeomsGenHelper is a module of PROFFASTpylot.

It contains several helper routines for the generation of
hdf5 files.

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

import yaml
import os
import re
import math
import glob
import datetime as dt
import numpy as np
import pandas as pd
from prfpylot.prepare import Preparation
from prfpylot.filemover import FileMover


class GeomsGenHelper:
    def __init__(self, geomsgen_inputfile):
        self.logger = Preparation.create_logger(self, logginglevel="info")

        self.n_removed_values = 0
        # Read the input file.
        # Contains additional information to create the geoms file
        with open(geomsgen_inputfile, "r") as f:
            self.input_args = yaml.safe_load(f)
        self.input_file = geomsgen_inputfile

        if self.input_args["prf_res_path"] is not None:
            self.prf_res_path = self.input_args["prf_res_path"]
        else:
            self.prf_res_path = "results"  # ???

        self.result_folder = self.prf_res_path
        self.geoms_res_path = os.path.join(self.prf_res_path, "raw_output_proffast")

        prf_input_filepath = os.path.join(self.prf_res_path, self.input_args["input_file_name"])

        self.ils_file = self.input_args.get("ils_file")

        with open(prf_input_filepath, "r") as f:
            prf_input_parms = yaml.safe_load(f)

        self.instrument_number = prf_input_parms["instrument_number"]
        self.site_name = prf_input_parms["site_name"]

        # Path of output files:
        self.geoms_out_filename = "_".join([self.site_name, self.instrument_number, "GEOMS_OUT.h5"])
        if self.input_args["geoms_out_path"] is not None:
            self.geoms_out_path = self.input_args["geoms_out_path"]
        else:
            self.geoms_out_path = os.getcwd()
        os.makedirs(self.geoms_out_path, exist_ok=True)

        # move and relink logfile to result folder
        self.logfile_folder = os.path.join(self.geoms_out_path, "logfiles")
        os.makedirs(self.logfile_folder, exist_ok=True)
        FileMover._move_logfile(self)

        self.geoms_start_date = self.input_args["geoms_start_date"]
        self.geoms_end_date = self.input_args["geoms_end_date"]
        self.ils_filelist_warning = False
        self.ils_not_in_file_warning = False

    def _get_correction_factors(self):
        """Returns a dict containing the correction factors for the gases"""
        # This dict is only a preliminary version.
        # In the final version it is read in from a file.
        df = pd.read_csv(self.input_args["calibration_params_list"], skipinitialspace=True)
        # Strip the whitespaces from the column names:
        newCols = {}
        for key in df.keys():
            newCols[key] = key.strip()
        df.rename(columns=newCols, inplace=True)
        # Get the factors of the correct instrument
        df = df.loc[df["Instrument"] == self.instrument_number]
        return df.iloc[0].to_dict()

    def _write_dataset(self, data, dataset_name, attributes):
        """
        Helper method to write a dataset to the file.
        Params:
            data (np.array): The data to be stored
            dataset_name (string): The name of the dataset
            attributes (dict): The attributes to be stored
        """
        dtst = self.MyHDF5.create_dataset(dataset_name, data=data, dtype="f")
        keys = ["VAR_FILL_VALUE", "VAR_VALID_MAX", "VAR_VALID_MIN", "_FillValue", "valid_range"]
        for key, value in attributes.items():
            if key in keys:
                dtst.attrs[key] = np.float32(value)
            else:
                dtst.attrs[key] = np.bytes_(value)
        return dtst

    def _write_dataset_src(self, data, dataset_name, attributes):
        """
        Helper method to write a dataset to the file.
        Params:
            data (np.array): The data to be stored
            dataset_name (string): The name of the dataset
            attributes (dict): The attributes to be stored
        """
        dtst = self.MyHDF5.create_dataset(dataset_name, data=data)
        for key, value in attributes.items():
            dtst.attrs[key] = np.bytes_(value)
        return dtst

    def _write_dataset_dt(self, data, dataset_name, attributes):
        """
        Helper method to write a dataset to the file.
        Params:
            data (np.array): The data to be stored
            dataset_name (string): The name of the dataset
            attributes (dict): The attributes to be stored
        """
        dtst = self.MyHDF5.create_dataset(dataset_name, data=data, dtype="f8")
        keys = ["VAR_FILL_VALUE", "VAR_VALID_MAX", "VAR_VALID_MIN", "_FillValue", "valid_range"]
        for key, value in attributes.items():
            if key in keys:
                dtst.attrs[key] = np.float64(value)
            else:
                dtst.attrs[key] = np.bytes_(value)
        return dtst

    def _get_pt_vmr_file(self, day, which):
        """
        Returns the path to the pt- or vmr-file of a specific day.
        If pt or vmr depends on the input of the `which` parameter.
        """
        if which not in ["pT", "VMR"]:
            self.logger.error("Parameter 'which' must be 'pT' or 'VMR'")
            return ""

        datestr = day.strftime("%y%m%d")
        file = os.path.join(
            self.result_folder,
            "raw_output_proffast",
            f"{self.site_name}{datestr}-{which}_fast_out.dat",
        )
        return file

    def _GEOMStoDateTime(self, times):
        """
        Transforms GEOMS DATETIME variable to dt.datetime instances
        (input is seconds, since 1/1/2000 at 0UT)
        """
        ntimes = []
        times = times / 86400.0
        t_ref = dt.date(2000, 1, 1).toordinal()

        for t in times:
            t_tmp = dt.datetime.fromordinal(t_ref + int(t))
            t_del = dt.timedelta(days=(t - math.floor(t)))

            ntimes.append(t_tmp + t_del)

        return np.array(ntimes)

    def _DateTimeToGEOMS(self, times):
        """
        Transforms dt.datetime instances to GEOMS DATETIME
        (output is seconds, since 1/1/2000 at 0UT)
        """
        gtimes = []

        t_ref = np.longdouble(dt.date(2000, 1, 1).toordinal())

        for t in times:
            t_h = np.longdouble(t.hour)
            t_m = np.longdouble(t.minute)
            t_s = np.longdouble(t.second)
            t_ms = np.longdouble(t.microsecond)
            t_ord = np.longdouble(t.toordinal())

            gtime = t_ord + (t_h + (t_m + (t_s + t_ms / 1.0e6) / 60.0) / 60.0) / 24.0 - t_ref

            gtimes.append(gtime * 86400.0)

        return np.array(gtimes)

    def apply_quality_checks(self, df):
        # check if the second CO channel exists
        CO_avg = df["XCO"].mean()
        if CO_avg == 0.0:
            df["XCO"] = [-900000.0] * len(df)

        # quality checks
        quality_check_passed = True
        for index, row in df.iterrows():
            if row["appSZA"] > self.input_args["QUALITY_FILTER_SZA"]:
                quality_check_passed = False
            if row["XAIR"] < self.input_args["QUALITY_FILTER_XAIR_MIN"]:
                quality_check_passed = False
            if row["XAIR"] > self.input_args["QUALITY_FILTER_XAIR_MAX"]:
                quality_check_passed = False

            for col in ["XH2O", "XCO2", "XCH4", "XCO"]:
                if row[col] in [np.nan, 0.0]:
                    quality_check_passed = False
                    self.logger.debug("line", index, "removed:", col, "=", row[col])

            # remove row from df
            if quality_check_passed is False:
                df = df.drop(index=index)
                self.n_removed_values += 1
                quality_check_passed = True

        # apply correction factors
        corr_fac = self._get_correction_factors()
        df["XCO2"] *= corr_fac["XCO2_cal"]
        df["XCH4"] *= corr_fac["XCH4_cal"]
        df["XH2O"] *= corr_fac["XH2O_cal"]
        df["XCO"] *= corr_fac["XCO_cal"]
        df["altim"] /= 1000.0

        # write fill value to values out of bounds
        df["XH2O"] = df["XH2O"].mask(df["XH2O"] <= 0.0)
        df["XH2O"] = df["XH2O"].mask(df["XH2O"] >= 10000.0)
        df["XCO2"] = df["XCO2"].mask(df["XCO2"] <= 0.0)
        df["XCO2"] = df["XCO2"].mask(df["XCO2"] >= 10000.0)
        df["XCH4"] = df["XCH4"].mask(df["XCH4"] <= 0.0)
        df["XCH4"] = df["XCH4"].mask(df["XCH4"] >= 10.0)
        df["XCO"] = df["XCO"].mask(df["XCO"] <= 0.0)
        df["XCO"] = df["XCO"].mask(df["XCO"] >= 10000.0)

        fill_value = -900000.0
        df.replace(np.nan, fill_value, inplace=True)

        # return none if less than 11 lines
        if len(df) < 11:
            return None
        else:
            self.logger.debug("Data filter applied... ", "file_len: ", len(df))
            return df

    def get_comb_invparms_df(self, day):
        """Get the complete path to the combined invparms file."""
        invparms_file = glob.glob(os.path.join(self.prf_res_path, "comb_invparms_*.csv"))[0]

        cols = [
            "UTC",
            "LocalTime",
            "JulianDate",
            "gndP",
            "gndT",
            "latdeg",
            "londeg",
            "altim",
            "appSZA",
            "azimuth",
            "XH2O",
            "XAIR",
            "XCO2",
            "XCH4",
            "XCH4_S5P",
            "XCO",
            "H2O",
            "O2",
            "CO2",
            "CH4",
            "CO",
            # "XCO2_STR",
            "CH4_S5P",
            # "H2O_rms",
            # "CO2_rms",
            # "CH4_rms",
            # "CO_rms",
        ]
        df = pd.read_csv(
            invparms_file, delimiter=",", skipinitialspace=True, parse_dates=["UTC", "LocalTime"]
        )

        df = df[cols]
        # drop all columns except the selected day
        for i, row in df.iterrows():
            current_date = row["LocalTime"].date()
            if current_date != day.date():
                df.drop(index=i, inplace=True)

        df = self.apply_quality_checks(df)
        return df

    def get_datetimes(self):
        datetime_list = []
        # out_path = self.geoms_out_path
        inp_path = self.geoms_res_path

        inv_list = glob.glob(os.path.join(inp_path, "*invparms*.dat"))  # invparms file list
        for file in inv_list:
            file = os.path.basename(file)
            file = re.sub(self.site_name, "", file)
            date = dt.datetime.strptime(
                "20" + file[0:2] + "-" + file[2:4] + "-" + file[4:6], "%Y-%m-%d"
            )
            datetime_list.append(date)

        return datetime_list

    def get_start_date(self):
        date = dt.datetime.strptime(str(self.geoms_start_date), "%Y-%m-%d")
        return date

    def get_end_date(self):
        date = dt.datetime.strptime(str(self.geoms_end_date), "%Y-%m-%d")
        return date
