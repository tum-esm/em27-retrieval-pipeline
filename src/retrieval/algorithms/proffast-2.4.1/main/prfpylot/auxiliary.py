"""Auxiliary is a module of PROFFASTpylot.

Hand the pressure and coordinates to PROFFAST, add own functions to handle
different data formats.

License information:
PROFFASTpylot - Running PROFFAST with Python
Copyright (C)   2022    Lena Feld, Benedikt Herkommer,
                        Karlsruhe Institute of Technology (KIT)

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

import pandas as pd
import datetime as dt
import glob
import os
import sys
import numpy as np
import yaml
import copy


class AuxiliaryHandler():
    """Parent class for reading, interpolating and averaging auxiliary data."""

    mandatory_options = [
        "dataframe_parameters",
        "filename_parameters",
        "data_parameters",
    ]

    default_options = {
        "utc_offset": 0.0
    }

    parsed_dtcol = "parsed_datetime"

    def __init__(
            self,
            description_file,
            data_path,
            dates,
            logger):

        self.dates = self.get_date_list(dates)

        self.logger = logger
        self.data_path = data_path

        with open(description_file, "r") as f:
            args = yaml.load(f, Loader=yaml.FullLoader)
        for option, value in args.items():
            self.__dict__[option] = value

        for option, default in self.default_options.items():
            if self.__dict__.get(option) is None:
                self.__dict__[option] = default
                self.logger.debug(
                    f"The parameter {option} was set to the default "
                    f"value: {default}.")

        for option in self.mandatory_options:
            if self.__dict__.get(option) is None:
                self.logger.critical(
                    f"Mandatory parameter {option} not given in the "
                    f"description file {description_file}!")
                sys.exit()
            else:
                # fill defaults and check for missing values inside the dicts
                self.__dict__[option] = self._set_defaults(option)
        self._check_mandatory()

        self.cols_to_use = []
        for key in ["time_key", "date_key", "datetime_key"]:

            val = self.dataframe_parameters[key]
            if val != "":
                self.cols_to_use.append(val)

        # to ensure the date-columns are read in as string format
        self.dataframe_parameters["csv_kwargs"] = \
            self._append_dtype_to_csv_kwargs()

    def get_date_list(self, dates):
        """Return extended, sorted deepcopy of date_list."""

        # make a deepcopy of the dates since we want to add one day at the end
        # and the beginning of the list. And since lists are mutable in python
        # therefore are kind of `called by reference`, it is necessary to
        # explicitly deepcopy it here.
        dates = copy.deepcopy(dates)
        dates = self._extend_datelist(dates)
        # delete the duplicate days:
        dates = list(set(dates))
        dates = sorted(dates)
        return dates

    def create_df(self):
        """Read relevant files and return dataframe.

        This function was formerly called _read_subdaily_files()."""

        # in case the date information is only given in the file name
        datetime_key = self.dataframe_parameters["datetime_key"]
        date_key = self.dataframe_parameters["date_key"]
        if datetime_key == "" and date_key == "":
            df = self.create_df_when_date_in_filename()
            return df

        file_list = self._get_file_list(self.dates)
        df = self.concat_files(file_list)
        df = self._parse_datetime_col(df)
        df = df.sort_values(self.parsed_dtcol).drop_duplicates()
        df = df.reset_index(drop=True)
        return df

    def concat_files(self, file_list):
        # read all files from list and concatenate them
        df = pd.DataFrame()
        for file in file_list:
            self.logger.debug(f"Read in file {file}")
            temp = pd.read_csv(
                file,
                usecols=self.cols_to_use,
                **(self.dataframe_parameters["csv_kwargs"]))
            df = pd.concat([df, temp])
        return df

    def create_df_when_date_in_filename(self):
        """Create dataframe if date information is only given in the file name.
        """
        dataframes = []
        for date in self.dates:
            file_list = self._get_file_list([date])
            if len(file_list) == 0:
                self.logger.warning(
                    "No pressure file could be found "
                    f"at {date.strftime('%Y-%m-%d')}")
            tmp = self.concat_files(file_list)
            tmp = self._parse_datetime_col(tmp, date)
            dataframes.append(tmp)
        df = pd.concat(dataframes)
        df = df.sort_values(self.parsed_dtcol).drop_duplicates()
        df = df.reset_index(drop=True)
        return df

    def get_frequency(self, df):
        differences = df[self.parsed_dtcol].diff().dropna()
        frequency = differences.median()
        return frequency

    def interpolate_data_at(self, df, utc_time, data_key):
        """Return interpolated value for given date_key and time stamp.

        If time difference greater than threshhold, return None.
        """
        time_key = self.parsed_dtcol

        if self._is_below_threshold(df, utc_time) is False:
            return None

        interpolated = np.interp(
            np.datetime64(utc_time, "ns"),
            df[time_key].astype("datetime64[ns]"),
            df[data_key].values)

        return interpolated

    def _is_below_threshold(self, df, utc_time):
        """Reject if time difference to closed value is greater than threshold.

        Get the two closest entries by calculating differences to current value
        Return False if distance greater, than threshold, and else True.
        """

        x = df[self.parsed_dtcol].values.astype("datetime64[ns]")
        x_i = np.datetime64(utc_time)

        # Find the index where the value would be inserted to maintain order
        idx = np.searchsorted(x, x_i)

        # Calculate distances to the closest x values
        if idx == 0:
            closest_idx = 0
        elif idx == len(x):
            closest_idx = len(x) - 1
        else:
            closest_idx = idx if abs(x[idx] - x_i) < abs(x[idx - 1] - x_i) \
                else idx - 1

        distance = abs(x[closest_idx] - x_i)

        # distance in seconds
        distance = distance.astype('timedelta64[s]').astype(int)

        # compare to threshold
        threshold = self.max_interpolation_time * 3600
        if distance > threshold:
            self.logger.debug(
                f"Interpolation time for requested time {utc_time} "
                "was larger than the threshold. Will skip the processing "
                "of the spectra corresponding to this time. "
                "(See next message!)")
            return False
        else:
            return True

    def _extend_datelist(self, dates):
        """Add additional day before and after time range.
        To prevent time zone issues."""

        previous_day = dates[0] - dt.timedelta(days=1)
        dates.append(previous_day)
        next_day = dates[-1] + dt.timedelta(days=1)
        dates.append(next_day)

        return dates

    def _get_file_list(self, dates):
        """Return merged filename of pressure_type."""
        params = self.filename_parameters
        file_list = []
        for date in dates:
            filename = "".join(
                    [params["basename"],
                        date.strftime(params["time_format"]),
                        params["ending"]]
                )
            path = os.path.join(
                self.data_path, filename)
            tmp_file_list = glob.glob(path)
            file_list.extend(tmp_file_list)

        # remove duplicates
        file_list = list(set(file_list))

        # warning in case of empty file list
        if len(dates) > 1 and len(file_list) == 0:
            # no pressure file is available
            self.logger.warning(
                "No pressure file could be found.")
        return file_list

    def _parse_datetime_col(self, df, date=None):
        """Parse the dataframe for a suitable datetime.

        Add the column 'parsed_datecol' to the dataframe
        Depending on the options given, the datetime column is constructed f
        rom the combination of the separate time and date columns.

        Parameters:
            df (pandas.DataFrame): pressure dataframe containing time
                information in arbitrary format.

        Returns:
            df (pandas.DataFrame): with an additional datetime column.

        """
        # give warning if an empty df is read in and this is not the first
        # or the last day of the list
        # (since these are only to catch dateline issues)
        # if len(df) == 0:
        #     if not (date == self.dates[0] or date == self.dates[-1]):
        #         self.logger.warning(
        #             f"For date {date} an empty dataset is read in!")
        #         return df
        #     else:
        #         return df
        df_args = self.dataframe_parameters
        time_key = df_args["time_key"]
        time_fmt = df_args["time_fmt"]
        date_key = df_args["date_key"]
        date_fmt = df_args["date_fmt"]
        dt_key = df_args["datetime_key"]
        dt_fmt = df_args["datetime_fmt"]

        if dt_key == "":
            # no datetime column available, check for date column:
            if date_key == "":
                # no date key avaliable as well. Do only take the time from
                # file.
                # day is taken from call day
                try:
                    df[self.parsed_dtcol] = pd.to_datetime(
                        df[time_key], format=time_fmt)
                except KeyError:
                    self.logger.critical(
                        f"Could not access key {time_key} in pressure data."
                        "Exit Program.")
                    exit()

                df[self.parsed_dtcol] = df[self.parsed_dtcol].apply(
                    lambda x: x.replace(
                        day=date.day, month=date.month, year=date.year))
            else:
                # combine two columns to datetime
                try:
                    df[self.parsed_dtcol] = pd.to_datetime(
                        df[date_key] + df[time_key],
                        format=date_fmt+time_fmt)
                except KeyError:
                    self.logger.critical(
                        f"Could not find key {date_key} or {time_key} in "
                        f"pressure data for date {date}. Exit Program.")
                    self.logger.debug(f"The dataframe is: {df}")
                    exit()
        else:
            # seems that a datetime column is available:
            try:
                if dt_fmt == "POSIX-timestamp":
                    df[self.parsed_dtcol] = df[dt_key].apply(
                        lambda x: dt.datetime.utcfromtimestamp(np.float64(x)))
                else:
                    df[self.parsed_dtcol] = pd.to_datetime(
                        df[dt_key], format=dt_fmt)
            except KeyError:
                self.logger.critical(
                    f"Could not find key {dt_key} in pressure data."
                    f"Pressure data are:\n{df}\n."
                    f"Pressure folder is: {self.data_path}\n"
                    "Exit Program.")
                exit()

        # remove time zone information
        df[self.parsed_dtcol] = df[self.parsed_dtcol].dt.tz_localize(None)

        # convert to UTC
        df[self.parsed_dtcol] -= pd.Timedelta(hours=self.utc_offset)
        return df

    def _set_defaults(self, option):
        """Set defaults in dataframe, filename and data parameters dict.
        Check for mandatory options.

        Parameters:
            option (str): "dataframe_parameters", "filename_parameters"
                or "data_parameters"

        Return:
            modified dict
        """
        defaults = {}
        defaults["data_parameters"] = {
            "max_pressure": 1500,
            "min_pressure": 500,
            "default_value": "skip"
        }
        defaults["dataframe_parameters"] = {
            "pressure_key": "",
            "time_key": "",
            "time_fmt": "",
            "date_key": "",
            "date_fmt": "",
            "datetime_key": "",
            "datetime_fmt": "",
            "csv_kwargs": {},
        }
        defaults["filename_parameters"] = {
            "basename": "",
            "time_format": "",
            "ending": ""
        }

        d = self.__dict__[option]
        if option not in defaults.keys():
            return d
        for k, v in defaults[option].items():
            if d.get(k) is None:
                d[k] = v
                self.logger.debug(
                    f"The pressure parameter {option}:{k} was set to "
                    f"default value: {v}.")
        return d

    def _check_mandatory(self):
        """Check mandatory options for completeness.

        The options must satisfy the following:
        - the time key XOR datetime key is given and
        - the filename is not empty.

        Raises:
            RuntimeError: in case of a missing option.

        """

        # time or datetime key
        time_key = self.dataframe_parameters.get("time_key")
        datetime_key = self.dataframe_parameters.get("datetime_key")
        general_instruction = (
            " Give either the time_key or the datetime_key in "
            "dataframe_parameters!")
        if (time_key == "") and (datetime_key == ""):
            raise RuntimeError(
                "None of time_key and datetime_key are given!"
                + general_instruction)
        elif (time_key != "") and (datetime_key != ""):
            raise RuntimeError(
                "time_key and datetime_key can not be given at the same time!"
                + general_instruction)

        # filename not empty
        joined_filename = "".join([
            self.filename_parameters["basename"],
            self.filename_parameters["time_format"],
            self.filename_parameters["ending"]
        ])
        if joined_filename == "":
            raise RuntimeError(
                "No filename is given! Give the start, time format (optional) "
                "and ending of your filename as filename_parameters: "
                "basename, time_format and ending.")

    def _append_dtype_to_csv_kwargs(self):
        """Return extended csv_kwargs to make sure the date and time column
        are interpreted as string."""
        csv_kwargs = self.dataframe_parameters["csv_kwargs"]
        dtype = {
            self.dataframe_parameters["date_key"]: str,
            self.dataframe_parameters["time_key"]: str,
            self.dataframe_parameters["datetime_key"]: str,
        }
        dtype.pop("", None)  # remove default empty string

        csv_kwargs["dtype"] = dtype
        return csv_kwargs


class CoordHandler(AuxiliaryHandler):
    """Organize variable coordinates from a file for a moving observer"""

    default_options = {
        "utc_offset": 0.0,
        "altitude_factor": 1.0,
        "data_parameters": {},
        "max_interpolation_time": 0.167,  # 10 min in hours
    }

    def __init__(
            self, coord_type_file, coord_path, dates, logger,
            static_coords=None):
        super().__init__(
            description_file=coord_type_file,
            data_path=coord_path,
            dates=dates,
            logger=logger,
            )
        self.static_coords = static_coords
        for key in ["latitude_key", "longitude_key", "altitude_key"]:
            dataframe_key = self.dataframe_parameters.get(key)
            if dataframe_key is not None:
                self.cols_to_use.append(dataframe_key)

    def prepare_coord_df(self):
        df = self.create_df()
        for coord_type in ["latitude", "longitude", "altitude"]:
            if self.dataframe_parameters.get(coord_type+"_key") is None:
                df = self.add_static_coord(df, coord_type)
        self.coord_df = df

    def add_static_coord(self, df, coord_type):
        """Use static coordinates if one of the coordinates is not given."""
        if self.static_coords is None:
            raise RuntimeError(
                f"Give static coords if no {coord_type} key is present in "
                "your coord data")
        static_coord = self.static_coords[coord_type[0:3]]
        static_coord_column = [static_coord]*len(df)
        df[f"static_{coord_type}"] = static_coord_column
        self.dataframe_parameters[coord_type+"_key"] = "static_" + coord_type

        self.logger.warning(
            f"No {coord_type} is given for the mobile coordinates. "
            f"The static {coord_type} of {static_coord} km is used"
            " for all interferograms. Make sure that this altitude is "
            "representative for all observations.")
        return df

    def get_coords_at(self, utc_time):
        """Return coordinates at given utc time."""
        coords = []
        frequency = self.get_frequency(self.coord_df)
        if frequency >= pd.Timedelta("30s"):
            coords = self.interpolate_coords(utc_time)
        else:
            coords = self.average_coords(utc_time)

        if coords is not None:
            coords = self._apply_altitude_factor(coords)
        return coords

    def interpolate_coords(self, utc_time):
        coords = []
        for coord_name in ["latitude", "longitude", "altitude"]:
            data_key = self.dataframe_parameters[coord_name+"_key"]
            coord_value = self.interpolate_data_at(
                self.coord_df, utc_time, data_key)
            if coord_value is None:
                return None
            coords.append(coord_value)
        return coords

    def average_coords(self, utc_time):
        coords = []
        df = self._get_timeslice(utc_time)
        if len(df) == 0:
            return None
        for coord_name in ["latitude", "longitude", "altitude"]:
            data_key = self.dataframe_parameters[coord_name+"_key"]
            coord_value = df[data_key].mean()
            coords.append(coord_value)
        return coords

    def _apply_altitude_factor(self, coords):
        return [coords[0], coords[1], coords[2]*self.altitude_factor]

    def _get_timeslice(self, utc_time):
        # TODO: does the utc_time refer to the beginning?
        time_slice = slice(
            pd.Timestamp(utc_time),
            pd.Timestamp(utc_time) + pd.Timedelta("60s")  # measurement period
            )
        df = self.coord_df.set_index(self.parsed_dtcol).sort_index()

        return df[time_slice]


class PressureHandler(AuxiliaryHandler):
    """Read, interpolate and return pressure data from various formats."""

    default_options = {
        "utc_offset": 0.0,
        "pressure_factor": 1.0,
        "pressure_offset": 0.0,
        "data_parameters": {},
        "max_interpolation_time": 2,  # in hours
    }

    parsed_dtcol = "parsed_datetime"

    def __init__(
            self, pressure_type_file, pressure_path, dates, logger):
        """
        Initialize the Pressure Handler.
        Parameters:
            pressure_type_file(str): path to the pressure config file
            pressure_path(str): path to the folder where the pressure files
                                are located.
            dates(list of datetime-objects): A list of all days supposed to
                                                be processed. Use the same list
                                                as generated by the
                                                PROFFASTpylot
        """
        super().__init__(
            description_file=pressure_type_file,
            data_path=pressure_path,
            dates=dates,
            logger=logger,
            )

        # check if pressure key is given
        pressure_key = self.dataframe_parameters.get("pressure_key")
        if pressure_key == "":
            raise RuntimeError(
                "The key of the pressure column in the pressure file must be "
                "given as dataframe_parameters: pressure_key")

        # For a later read in of the pressure data frame it makes sense to only
        # read in the columns needed. In case of large meteo files, this can
        # save a lot of RAM and processing time.
        self.cols_to_use.append(self.dataframe_parameters["pressure_key"])

        self.p_df = pd.DataFrame()

    def prepare_pressure_df(self):
        """Read the pressure of a day, from files with a various frequencies.

        The dataframe self.p_df is created as a object of the pressure_handler
        instance Containing the pressure and a datetime column.

        The pressure column is multiplied by the pressure_factor given in the
        pressure input file.

        """
        self.logger.debug("Execute prepare_pressure_df()...")

        self.p_df = self.create_df()
        self._filter_pressure()
        self._apply_pressure_offset_and_factor()
        self._check_frequency()

        # print df.head for debug purposes
        df_args = self.dataframe_parameters
        p_key = df_args["pressure_key"]
        df_print = self.p_df[[self.parsed_dtcol, p_key]]
        self.logger.debug(
            "Created pressure DataFrame:\n\n"
            "# start of self.p_df #\n"
            f"{df_print.head()}\n"
            )

    def get_pressure_at(self, utc_time):
        """Return the interpolated pressure at a given time.

        If the value is rejected or an interpolation error occured p=0
        is returned.The corresponding spectra will not be processed.
        This is determined in prepare.get_spectra_pT_input().

        If the pressure measurements for a whole day is missing, the whole
        day is deleted from the processing list in pylot.run_inv().

        Parameters:
            pressure_time (datetime:datetime):
                time in timezone of the pressure file
        """
        p_key = self.dataframe_parameters["pressure_key"]
        p = self.interpolate_data_at(self.p_df, utc_time, p_key)
        return p

    def _check_frequency(self):
        frequency = self.get_frequency(self.p_df)
        if frequency < pd.Timedelta("30s"):
            self.logger.warning(
                "The pressure is recorded with a frequency higher than 30s. "
                "Please note that the pressure is interpolated by "
                "PROFFASTpylot. Consider to average your pressure data over a "
                "longer time period."

                )

    def _filter_pressure(self, date=None):
        """
        Parse the internal raw p_df and eliminate bad values
        """
        df_args = self.dataframe_parameters
        p_key = df_args["pressure_key"]
        # Filter values which are too large or too small.
        # Replace or remove them.
        maxVal = float(self.data_parameters["max_pressure"])
        minVal = float(self.data_parameters["min_pressure"])
        replace_val = 0
        if self.data_parameters["default_value"] == "skip":
            replace_val = np.nan
        else:
            replace_val = float(self.data_parameters["default_value"])
        self.p_df[p_key] = np.where(
            self.p_df[p_key] > maxVal, replace_val, self.p_df[p_key])
        self.p_df[p_key] = np.where(
            self.p_df[p_key] < minVal, replace_val, self.p_df[p_key])
        self.p_df = self.p_df.dropna(subset=[p_key])

    def _apply_pressure_offset_and_factor(self):
        """Multiply the pressure column with the pressure factor."""
        pressure_key = self.dataframe_parameters["pressure_key"]
        self.p_df[pressure_key] *= self.pressure_factor
        self.p_df[pressure_key] += self.pressure_offset
