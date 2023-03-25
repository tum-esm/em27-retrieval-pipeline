"""Prepare is a module of PROFFASTpylot.

Initialasation, handling of all parameters, generation of the
PROFFAST input files.

License information:
PROFFASTpylot - Running PROFFAST with Python
Copyright (C)   2022    Lena Feld, Benedikt Herkommer,
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

import prfpylot
from prfpylot.pressure import PressureHandler
import os
import sys
import yaml
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
from glob import glob
import logging
from timezonefinder import TimezoneFinder
import pytz
import fortranformat
import inspect
import codecs
from random import randint


class Preparation():
    """Import input parameters, and create input files."""

    template_types = {
        "prep": "preprocess4",
        "tccon": "tccon",
        "inv": "invers20",
        "pcxs": "pcxs20"
    }

    mandatory_options = [
        "instrument_number",
        "site_name",
        "site_abbrev",
        "map_path",
        "pressure_path",
        "pressure_type_file",
        "interferogram_path",
        "analysis_path",
        "result_path",
    ]

    defaults = {
        "note": "",
        "utc_offset": 0.0,
        "start_with_spectra": False,
        "delete_abscosbin_files": False,
        "delete_input_files": False,
        "backup_results": True,
        "min_interferogram_size": 3.7,
        "tccon_mode": False,
        "ggg2020mapfiles": False,  # do not give in input file!
        "ils_parameters": None
    }

    def __init__(self, input_file, logginglevel="info"):
        self.logger = self.get_logger(logginglevel=logginglevel)
        self.logger.info(
            "++++ Welcome to PROFFASTpylot ++++")
        self.logger.debug("Start reading input file...")

        # read input file
        with open(input_file, "r") as f:
            args = yaml.load(f, Loader=yaml.FullLoader)

        for option, value in args.items():
            self.__dict__[option] = value

        for option in self.mandatory_options:
            if self.__dict__.get(option) is None:
                self.logger.critical(
                    f"Mandatory option {option} not given in the input file"
                    f" file {input_file}!")
                sys.exit()

        for option, value in self.defaults.items():
            if args.get(option) is None:
                self.__dict__[option] = value
                self.logger.debug(
                    f"{option} was set to default value: {value}."
                    )

        self.input_file = input_file

        # inspect.getsourcefile needes __init__.py!
        self.prfpylot_path = os.path.dirname(inspect.getsourcefile(prfpylot))

        # define full path <analysis>/<site>_<instrument_nr>
        self.analysis_instrument_path = os.path.join(
                    self.analysis_path,
                    f"{self.site_name}_{self.instrument_number}")

        # path to the PROFFAST executables
        if args.get("proffast_path") is None:
            head, _ = os.path.split(self.prfpylot_path)
            self.proffast_path = os.path.join(head, "prf")
        if not os.path.exists(self.proffast_path):
            self.logger.critical(
                    "PROFFAST does not exist! Make sure to download PROFFAST "
                    "before running PROFFASTpylot. Either copy it to "
                    "proffastpylot/prf or specify the path "
                    "where it is located.")
            sys.exit()

        # list of dates
        self.dates = self.get_dates(
                start_date=args["start_date"],
                end_date=args["end_date"]
            )

        # make relative paths absolute
        paths = [
            "map_path", "pressure_path", "pressure_type_file",
            "interferogram_path", "analysis_path", "result_path",
            "analysis_instrument_path"]
        for path in paths:
            self.__dict__[path] = os.path.abspath(self.__dict__[path])

        # coordinates
        self.coords = self.get_coords(args)

        # ILS-File is hardcoded since it will be released with prfpylot
        self.ils_file = os.path.join(self.prfpylot_path, 'ILSList.csv')

        # ILS parameters; if set in input file
        if self.ils_parameters is not None:
            self.ils_parameters = tuple(self.ils_parameters)
            # check for correct length
            if len(self.ils_parameters) != 4:
                raise ValueError(
                    "You must either give all 4 ILS Parameters, or None."
                    f"Given ILS Parameters were {self.ils_parameters}.")
            self.logger.warning(
                "Individual ILS Parameters were used, the parameters were not "
                "taken from the official COCCON ILS list!\n"
                f"Used ILS Parameters: {self.ils_parameters}.")

        # check if tccon mode is activated. Raise warning if it is activated
        if self.tccon_mode is True:
            self.tccon_mode = True
            self._tccon_mode_warning()
            if args.get("tccon_setting") is None:
                self.logger.critical("Give TCCON setting in TCCON mode!")
                sys.exit()

        dt_format = "%y%m%d"
        result_foldername = "{}_{}_{}-{}".format(
            self.site_name,
            self.instrument_number,
            self.dates[0].strftime(dt_format),
            self.dates[-1].strftime(dt_format))
        self.result_folder = os.path.join(self.result_path, result_foldername)

        # log of the processes
        self.logfile_path = os.path.join(
            self.result_folder, "logfiles")

        # calculate the _localtime_offset
        self._localtime_offset = self._get_localtime_offset()

        # initialise pressure handler
        self.pressure_handler = PressureHandler(
            self.pressure_type_file, self.pressure_path,
            self.dates, self.logger)

        # collect all generated input files to move in FileMover
        self.global_inputfile_list = []

        self.logger.debug("Finished reading of input file.")

    def get_logger(self, logginglevel="info"):
        """Create and return a logger."""
        r = str(randint(10000, 99999))
        logger = logging.getLogger(r)
        # set logging to debug to record everything in the first place
        logger.setLevel(logging.DEBUG)
        StreamHandler = logging.StreamHandler()
        cwd = os.getcwd()
        logfile_name = f"pylot_{r}.log"
        self.pylot_log = os.path.join(cwd, logfile_name)
        FHandler = logging.FileHandler(logfile_name, mode='w')

        if logginglevel == "debug":
            StreamHandler.setLevel(logging.DEBUG)
            FHandler.setLevel(logging.DEBUG)
        elif logginglevel == "info":
            StreamHandler.setLevel(logging.INFO)
            FHandler.setLevel(logging.INFO)
        elif logginglevel == "warning":
            StreamHandler.setLevel(logging.WARNING)
            FHandler.setLevel(logging.WARNING)

        logger.addHandler(StreamHandler)
        logger.addHandler(FHandler)
        StreamFormat = logging.Formatter(
            '{asctime}, {levelname}: {message}',
            style='{')
        StreamHandler.setFormatter(StreamFormat)
        FHandler.setFormatter(StreamFormat)

        logger.debug(f"Initialized logger with random number {r}.")
        return logger

    def get_dates(self, start_date=None, end_date=None):
        """Return a list of dates for the given site, instrument.
        Truncate the list if start_date and end_date are given.

        Params:
            start_date (dt.date): optional start date
            end_date (dt.date): optional end date
        """
        if self.start_with_spectra is False:
            self.logger.debug(
                "Searching for all interferogram folders ...")
            datapath = os.path.join(self.interferogram_path, "*")
        elif self.start_with_spectra is True:
            self.logger.debug(
                "Searching for all spectra folders ...")
            datapath = os.path.join(self.analysis_instrument_path, "*")

        dates = self._create_datelist(datapath)
        if len(dates) == 0:
            self.logger.critical(
                f"No interferograms were found at {self.interferogram_path}!")
            sys.exit()

        date_str_list = [date.strftime("%y-%m-%d") for date in dates]
        self.logger.debug(
            f"The following dates were found at {datapath[:-2]}: "
            f"{', '.join(date_str_list)}")

        if start_date is not None:
            i = self._get_start_date_pos(start_date, dates)
            dates = dates[i:]
        if end_date is not None:
            i = self._get_end_date_pos(end_date, dates)
            dates = dates[:i]

        print_date_list = [d.strftime("%Y-%m-%d") for d in dates]
        print_date_str = ", ".join(print_date_list)

        # print run information
        self.logger.info(
            "Run information:\n"
            f"Retrieval for Instrument {self.instrument_number} "
            f"at {self.site_name} with time offset {self.utc_offset}.\n"
            "The following dates will be processed:\n"
            f"{print_date_str}.\n")

        return dates

    def get_coords(self, args):
        """Return dict of coords.

        Params:
            args: all arguments that have been read from the input file.
        """
        coord_error = (
            "Give the coordinates in the input file or specify a "
            "coordinate file!"
            )
        coords = args["coords"]
        if None in args["coords"].values():
            if args.get("coord_file") is None:
                self.logger.critical(coord_error)
                sys.exit()
            coords = self.get_coords_from_file(self.dates[0])
            # check for consistent coordinates in measurement period
            last_coords = self.get_coords_from_file(self.dates[-1])
            if last_coords != coords:
                self.logger.critical(
                    f"Coordinates at the start date {coords} do not match "
                    f"the coordinates at the end date {last_coords}!"
                    "PROFFASTpylot can not preprocess data from different "
                    "sites in one run! Please adapt the start and end date.")
                sys.exit()
        if None in coords.values():
            self.logger.critical(coord_error)
            sys.exit()

        return coords

    def _create_datelist(self, path):
        """Create datelist of given path.
        Skip elements that are not folders of the format "YYMMDD".
        """
        date_paths = glob(path)

        dates = []
        for date_path in date_paths:
            date_str = os.path.split(date_path)[1]

            if not os.path.isdir(date_path):
                self.logger.debug(
                    f"Skipping invalid element in datelist: {date_str}. "
                    "No Directory!")
                continue
            try:
                date = dt.strptime(date_str, "%y%m%d")
            except ValueError:
                self.logger.debug(
                    f"Skipping invalid element in datelist: {date_str}. "
                    "Could not parse date!")
                continue

            dates.append(date)

        dates.sort()
        return dates

    def get_template_path(self, template_type):
        """Return path to the corresponding template file."""
        folder_path = os.path.join(self.prfpylot_path, "templates")
        filename = "template_{}.inp".format(self.template_types[template_type])
        template_path = os.path.join(folder_path, filename)
        return template_path

    def get_prf_input_path(self, template_type, date=None):
        """Return path to the corresponding prf_input_file."""
        if template_type in ["pcxs", "inv"]:
            folder_path = os.path.join(self.proffast_path, "inp_fast")
            date_str = dt.strftime(date, "%y%m%d")
            filename = "".join(
                [self.template_types[template_type],
                    f"{self.site_name}_{date_str}.inp"]
            )
        elif template_type == "prep":
            folder_path = os.path.join(self.proffast_path, "preprocess")
            date_str = dt.strftime(date, "%y%m%d")
            filename = "".join(
                [self.template_types[template_type],
                    f"{self.site_name}_{date_str}",
                    ".inp"]
                )
        elif template_type == "tccon":
            folder_path = os.path.join(self.proffast_path, "preprocess")
            filename = "".join([self.template_types[template_type], ".inp"])

        prf_input_path = os.path.join(folder_path, filename)
        return prf_input_path

    ''' # probably not needed anymore
    def get_map_file(self, date):
        """Return path to mapfile of given date.

        params:
            date: datetime object
        """
        search_string = os.path.join(
            self.map_path,
            "*{date}.map".format(date=date.strftime("%y%m%d")))
        map_file = glob(search_string)

        assert len(map_file) == 1
        map_file = map_file[0]

        return map_file
    '''

    def generate_prf_input(self, template_type, date=None):
        """Generate a template file.

        Calling the corresponding collect parameters function
        and replace template function.

        params:
            template_type (str): Can be "prep", "tccon", "pt", "inv" or "pcxc"

        Return:
            prf_input_file(s) (str, list of str or None):
                In case of inverse multiple input
                files are created if spectra of one measurement day belong to
                different map files. If no spectra are, return None
        """
        # the name of the input file to be generated
        prf_input_file = self.get_prf_input_path(template_type, date)

        if date is not None:
            date_str = dt.strftime(date, "%y%m%d")

        if template_type == "prep":
            self.logger.debug(
                f"Generating preprocess inp file for {date_str}..")
            parameters = self.get_prep_parameters(date)
            if parameters["igrams"] == "":
                return None

        elif template_type == "tccon":
            parameters = {"tccon_setting": self.tccon_setting}

        elif template_type == "pcxs":
            parameters = self.get_pcxs_parameters(date)
            self.logger.debug(
                f"Generating {self.template_types[template_type]}"
                f" inp file for {date_str}..")

        elif template_type == "inv":
            self.logger.debug(
                f"Generating {self.template_types[template_type]}"
                f" inp file for {date_str}..")
            parameters = self.get_inv_parameters(date)
            prf_input_files = []
            for parameter_i in parameters:
                suffix = parameter_i["SUFFIX"]
                prf_input_files.append(prf_input_file[:-4] + f"_{suffix}.inp")
                self.replace_params_in_template(
                    parameter_i, template_type, prf_input_files[-1])
            # safe inputfiles in global list to move/delete them later
            self.global_inputfile_list.extend(prf_input_files)
            # return several input files hence do it already here:
            return prf_input_files
        else:
            raise ValueError(f"Unknown template_type {template_type}")

        self.replace_params_in_template(
            parameters, template_type, prf_input_file)
        self.global_inputfile_list.append(prf_input_file)
        return prf_input_file

    def get_igrams(self, date):
        """Search for interferograms on disk and return a list of files."""
        date_str = date.strftime("%y%m%d")
        igrams = glob(os.path.join(self.interferogram_path, date_str, "*.*"))

        # skip all interferograms smaller than given limit
        temp_list = igrams[:]
        skipped_interferograms = False
        for igram in temp_list:
            filesize = os.path.getsize(igram) / (1024 * 1024)  # in MB
            if filesize < self.min_interferogram_size:
                igrams.remove(igram)
                self.logger.warning(
                    f"Interferogram {igram} has size "
                    f"{filesize} < {self.min_interferogram_size} MB "
                    "and will be skipped.")
                skipped_interferograms = True
        if skipped_interferograms is False:
            self.logger.debug(
                "No interferogram was skipped because of its filesize "
                f"at {date.date()}.")

        if igrams == []:
            self.logger.debug(f"No suitable Interferogram at day {date_str} "
                              "found in get_igrams().")
        return igrams

    def get_localdate_spectra(self):
        """Return dict linking all spectra to local dates.
        returns:
            {local_date: ["YYMMDD_HHMMSSSN.BIN", ...]}
        """
        all_spectra = []
        for date in self.dates:
            searchpath = os.path.join(
                self.analysis_instrument_path,
                date.strftime("%y%m%d"),
                "cal",
                "*SN.BIN")
            all_spectra.extend(glob(searchpath))
        all_spectra.sort()
        localdate_spectra = {}
        for spectrum in all_spectra:
            spectrum_name = os.path.basename(spectrum)
            meas_time, local_time, utc_time = self.get_times_of(
                spectrum=spectrum)
            local_date = local_time.date()
            if local_date in localdate_spectra.keys():
                localdate_spectra[local_date].append(spectrum_name)
            else:
                localdate_spectra[local_date] = [spectrum_name]
        return localdate_spectra

    def get_times_of(self, spectrum):
        """Read measurement time from filename, calculate local and utc time.
        Check if UTC time is consistent in the spectra header.

        Params:
            spectrum (str): full path to a spectrum

        Return:
            meas_time (dt.DateTime): time parsed from the filename
            local_time (dt.DateTime): calculated local time
            utc_time (dt.DateTime): read from spectra header
        """
        spectrum_name = os.path.basename(spectrum)
        meas_time = dt.strptime(spectrum_name, "%y%m%d_%H%M%SSN.BIN")
        local_time = meas_time + timedelta(hours=self._localtime_offset)

        # read UTC time from header
        with codecs.open(
                spectrum, "r", encoding="utf-8", errors="ignore") as f:
            header = f.readlines(1)[:24]
        UTh = float(header[13].strip())
        UT_date = header[12].strip()
        utc_time = dt.strptime(UT_date, "%y%m%d") + timedelta(hours=UTh)

        # check if times are consistent
        total_offset = self._localtime_offset + self.utc_offset
        pylot_utc_time = local_time - timedelta(hours=total_offset)

        # utc_time is shifted by half of the measurement time
        time_difference = (pylot_utc_time - utc_time).total_seconds()
        if abs(time_difference) > 300:  # not greater than 5 min
            self.logger.critical(
                f"Inconsistent times in spectrum {spectrum}!\n"
                f"UTC time of spectrum: {utc_time},\n"
                f"measurement time of spectrum: {meas_time},\n"
                f"local time of spectrum: {local_time}.\n"
                "Check if you entered the correct utc_offset or if there are "
                "files from another processing in the analysis folder!"
                )
            sys.exit()
        return meas_time, local_time, utc_time

    def replace_params_in_template(
            self, parameters, template_type, prf_input_file):
        """Generate a site specific input file by using a template.
        params:
            parameters(dict): containing keys which match the variable
                              names in the template file. They are replaced by
                              the entries.

            template_type(str): Can be "prep", "pt", "inv" or "pcxc"
            prf_input_file(str): the filename of the input file
        """
        templ_file = self.get_template_path(template_type)
        templ_stream = open(templ_file, 'r')
        prf_input_stream = open(prf_input_file, 'w')
        for line in templ_stream:
            new_line = line
            for key, parameter in parameters.items():
                new_line = new_line.replace(
                    '%{}%'.format(key), str(parameter))
                new_line = self._replace_backslash(new_line)

            prf_input_stream.write(new_line)
        templ_stream.close()
        prf_input_stream.close()
        if template_type == "tccon":
            self.tccon_file = prf_input_file

    def get_prep_parameters(self, date):
        """Return Parameters to be replaced in the pereprocess input file."""
        if self.ils_parameters is None:
            ME1, PE1, ME2, PE2 = self.get_ils_from_file(date)
        else:
            ME1, PE1, ME2, PE2 = self.ils_parameters
        lat = self.coords["lat"]
        lon = self.coords["lon"]
        alt = self.coords["alt"]
        comment = (
            "This spectrum is generated using preprocess4, a part of "
            "PROFFAST controlled by PROFFASTpylot.")
        if self.note is not None:
            comment = " ".join([comment, self.note])

        # get all good igrams
        igrams = self.get_igrams(date)
        igrams = "\n".join(igrams)
        # generate path to outputfolder for this date:
        datestring = date.strftime("%y%m%d")
        # NOTE: the 'cal' is necessary since "invers" automatically adds
        #       a "cal" string to the spectra path.
        outfolder = os.path.join(
            self.analysis_instrument_path, datestring, "cal")

        logfile = f"Internal_preprocess_log_{datestring}.log"

        parameters = {
            'ILS_Channel1': f"{ME1} {PE1}",
            'ILS_Channel2': f"{ME2} {PE2}",
            'site_name': self.site_name,
            'lat': lat,
            'lon': lon,
            'alt': alt,
            'utc_offset': str(self.utc_offset),
            'comment': comment,
            'igrams': igrams,
            'path_preprocess_log': self.logfile_path,
            'filename_logfile': logfile,
            'path_spectra': outfolder
                     }
        return parameters

    def get_pcxs_parameters(self, date):
        """Return parameters to replace in the pcxs20.inp file."""

        self.logger.debug("Create pcxs input parameters ...")

        lat = self.coords["lat"]
        lon = self.coords["lon"]
        alt = self.coords["alt"]

        parameters = {
            "ALT": alt,
            "LAT": lat,
            "LON": lon,
            "DATAPATH": self.analysis_instrument_path,
            "DATE": date.strftime("%y%m%d"),
            "SITE": self.site_name,
            "MAPPATH": self.map_path,
            "SITE_ABBREV": self.site_abbrev,
            "DATE_LONG": date.strftime("%Y%m%d"),
        }

        # set %WET_VMR% parameter
        #   GGG2014 map files: dry air (False)
        #   GGG2020 map files: wet air (True)
        if self.ggg2020mapfiles:
            parameters["WET_VMR"] = True
        else:
            parameters["WET_VMR"] = False
        return parameters

    def get_inv_parameters(self, date):
        """Return Parameters to replace in the invers20.inp file.
        Returns:
            parameters(list): contains one or two dict depending on measurement
                              time. See get_spectra_pT_input docstring.
        """
        spectra_pT_input = self.get_spectra_pT_input(date)
        parameters = []
        charlist = ["a", "b", "c", "d", "e"]
        for i, sub_pT_input in enumerate(spectra_pT_input):
            measurement_date = sub_pT_input[0][0:6]
            temp_parameters = {
                "DATAPATH": self.analysis_instrument_path,
                "MEASUREMENT_DATE": measurement_date,
                "LOCAL_DATE": date.strftime("%y%m%d"),
                "SITE": self.site_name,
                "SUFFIX": charlist[i],
                "SPECTRA_PT_INPUT": "\n".join(sub_pT_input)
            }
            parameters.append(temp_parameters)
        return parameters

    def get_spectra_pT_input(self, date):
        """Return a list of list of strings containing spectra and pT infos.
        If two UTC-Dates are found inside of one local day, spectra_pT_input
        contains two lists.

        YYMMDD_HHMMSSSN.BIN, pressure, T_PBL

        This function replaces the pt_intraday.inp file!
        Note that T_PBL is currently set to 0.0.

        params:
            (date): dt.Datetime, measurement time in local time or UTC time
        """
        spectra_list = self.localdate_spectra[date]
        spectra_list.sort()

        # in case of two UTC days in a local day list, split them up:
        spectra1 = []
        spectra2 = []
        first_date = dt.strptime(spectra_list[0][:6], "%y%m%d")
        spectra1.append(spectra_list[0])
        for spectrum in spectra_list[1:]:
            current_date = dt.strptime(spectrum[:6], "%y%m%d")
            if current_date != first_date:
                spectra2.append(spectrum)
            else:
                spectra1.append(spectrum)
        if len(spectra2) == 0:
            assert spectra_list == spectra1
            spectra_list = [spectra1]
        else:
            spectra_list = [spectra1, spectra2]

        spectra_pT_input = []
        for sublist in spectra_list:
            temp_pT_input = []
            for s in sublist:
                # get timestamp of spectrum
                # can be UTC or local time depending on measurement time
                timestamp = dt.strptime(s, "%y%m%d_%H%M%SSN.BIN")
                # apply a possible offset of the pressure data
                time_offset_p_igram = \
                    self.pressure_handler.utc_offset - self.utc_offset
                timestamp += timedelta(hours=time_offset_p_igram)
                # get pressure from mapfile
                p = self.pressure_handler.get_pressure_at(timestamp)

                temp_pT_input.append(f"{s}, {p}, 0.0")
            spectra_pT_input.append(temp_pT_input)

        return spectra_pT_input

    def get_ils_from_file(self, date):
        """Read the ILS parameters form the given file.

        Parameters:
            date (dt.datetime): If multiple ILS Parameters are given in the
                list, get the newest ILS parameters, that are already valid
                at date.

        Returns:
            ils_parameters (tuple): MEChan1, PEChan1, MEChan2, PEChan2
        """
        if self.tccon_mode:
            return (0.983, 0., 0.983, 0.)

        ils_df = pd.read_csv(self.ils_file, skipinitialspace=True)
        ils_df["ValidSince"] = pd.to_datetime(ils_df["ValidSince"])
        ils_df = ils_df.set_index("Instrument")

        try:
            ils_df = ils_df.loc[self.instrument_number]
        except KeyError:
            self.logger.critical(
                f"{self.instrument_number} is not in ILS-file.\n"
                "Please ensure you are using the newest version of "
                "PROFFASTpylot.\n"
                )
            sys.exit()
        if isinstance(ils_df, pd.Series):
            # this is the case, if only one entry per instrument is available
            MEChan1 = ils_df['Channel1ME']
            PEChan1 = ils_df['Channel1PE']
            MEChan2 = ils_df['Channel2ME']
            PEChan2 = ils_df['Channel2PE']
        elif isinstance(ils_df, pd.DataFrame):
            ils_df = ils_df.loc[ils_df["ValidSince"] <= date]
            row = ils_df.sort_values(by=["ValidSince"])
            MEChan1 = row["Channel1ME"].iloc[-1]
            MEChan2 = row["Channel2ME"].iloc[-1]
            PEChan1 = row["Channel1PE"].iloc[-1]
            PEChan2 = row["Channel2PE"].iloc[-1]
        else:
            self.logger.critical(
                "An unknown error occured while reading the "
                "ILS-list.")
            sys.exit()

        return (MEChan1, PEChan1, MEChan2, PEChan2)

    def get_coords_from_file(self, date):
        '''Return the coordinates from the coord file.'''
        coord_df = pd.read_csv(self.coord_file, skipinitialspace=True)
        coord_df["Starttime"] = pd.to_datetime(coord_df["Starttime"])
        coord_df = coord_df.set_index('Site')
        try:
            coord_df = coord_df.loc[self.site_name]
        except KeyError:
            self.logger.critical(f"{self.site_name} is not in coord.csv!")
            sys.exit()

        coords = {
            "lat": None,
            "lon": None,
            "alt": None
        }
        if isinstance(coord_df, pd.Series):
            # this is the case, if only one entry per site is available
            coords["lon"] = coord_df["Longitude"]
            coords["lat"] = coord_df["Latitude"]
            coords["alt"] = coord_df["Altitude_kmasl"]
        elif isinstance(coord_df, pd.DataFrame):
            coord_df = coord_df.loc[coord_df["Starttime"] <= date]
            row = coord_df.sort_values(by=["Starttime"])
            coords["lon"] = row["Longitude"].iloc[-1]
            coords["lat"] = row["Latitude"].iloc[-1]
            coords["alt"] = row["Altitude_kmasl"].iloc[-1]
        return coords

    def _get_start_date_pos(self, start_date, dates):
        """Return position of the start date in dates."""
        self.logger.debug("Locating the first date in the given interval.")
        start_date = dt.combine(start_date, dt.min.time())

        if start_date > dates[-1]:
            self.logger.error(
                "The start date is later than the date of the last "
                "interferogram on disk. Terminating program.")
            quit()
        else:
            for i, date in enumerate(dates):
                if date >= start_date:
                    return i

    def _get_end_date_pos(self, end_date, dates):
        """Return position of the end date in dates."""
        self.logger.debug("Locating the last date in the given interval.")
        end_date = dt.combine(end_date, dt.min.time())

        if end_date < dates[0]:
            self.logger.error(
                "The end date is earlier than the date of the first "
                "interferogram on disk. Terminating program.")
            quit()
        else:
            for i, date in enumerate(dates):
                if date == end_date:
                    return i+1
                if date > end_date:
                    return i

    def _replace_backslash(self, line):
        """Replace backslash with slash if run on linux."""
        if sys.platform == "linux":
            return line.replace("\\", "/")
        return line

    def prepare_map_file(self, date):
        """Generate map file if GGG2020 map file.
        Returns True if map files where found and created, False if no files
        where found.
        """
        # search for GGG2020 map files:
        srchstrg = f"{self.site_abbrev}*Z.map"
        mapfiles = glob(os.path.join(self.map_path, srchstrg))
        if len(mapfiles) != 0:
            self.logger.debug("Detected GGG2020 map files!")
            # GGG2020map files found!
            self.ggg2020mapfiles = True
            self._interpolate_map_files(date)
        else:
            srchstrg = f"{self.site_abbrev}{date.strftime('%Y%m%d')}.map"
            mapfiles = glob(os.path.join(self.map_path, srchstrg))
            if len(mapfiles) == 1:
                self.logger.debug("Detected GGG2014 map file!")
                self.ggg2020mapfiles = False
            else:
                self.logger.warning(
                    "No suitable map file found at "
                    f"{self.map_path} for {date.strftime('%Y-%m-%d')}.")
                return False
        return True

    def _interpolate_map_files(self, date):
        """Interpolate GGG2020 map files.
        Genereate a map file at 12:00 local time.
        This method is only called for mapfiles of type GGG2020.

        params:
            date (dt.datetime): datetime in local time (is called with
                elements of the localdate_spectra)
        """
        # create a timestamp of local noon
        noon_local = dt(
            year=date.year, month=date.month, day=date.day, hour=12)

        total_localtime_utc_offset = timedelta(
            hours=(self.utc_offset + self._localtime_offset))
        noon_utc = noon_local - total_localtime_utc_offset

        # List of all *.map files of the needed date
        search_str = (
            f"{self.site_abbrev}*{noon_utc.strftime('%Y%m%d')}*Z.map")
        mapfiles = glob(os.path.join(self.map_path, search_str))
        # add files of the following day
        # in case of interpolation between 21:00 and 00:00
        next_day = noon_utc + timedelta(hours=24)
        search_str = (
            f"{self.site_abbrev}_*_"
            f"{next_day.strftime('%Y%m%d')}*Z.map")
        mapfiles.extend(
             glob(os.path.join(self.map_path, search_str)))
        mapfiles.sort()
        # find the correct map files: bevore and after the hour of noon_utc
        i_noon = None  # local noon between i_noon and i_noon-1
        noon_hour = noon_utc.hour
        for i, file in enumerate(mapfiles):
            hour_file = int(file[-7:-5])
            if hour_file > noon_hour:
                i_noon = i
                break
        if i_noon in [None, 0]:
            self.logger.critical(
                f"Could not calculate mapfile for {noon_utc} UTC "
                "from the following files:\n"
                f"{' '.join(mapfiles)}"
                )

            sys.exit()

        file1 = pd.read_csv(
            mapfiles[i_noon-1],
            skipinitialspace=True,
            header=11)
        file1 = file1.to_numpy().transpose()
        file2 = pd.read_csv(
            mapfiles[i_noon],
            skipinitialspace=True,
            header=11)
        file2 = file2.to_numpy().transpose()

        # interpolate between the files
        # difference between two file is allways 3 hours
        tdiff = 3 * 60 * 60   # seconds
        # date of file 1 for the requested time diff
        print(mapfiles[i_noon-1])
        date_file1 = dt.strptime(
                    os.path.basename(mapfiles[i_noon-1])[-15:-5], "%Y%m%d%H")
        for i in range(file1.shape[0]):
            # do a linear interpolation, calculate everything in seconds:
            file1[i, :] = file1[i, :] + (file2[i, :] - file1[i, :]) / tdiff \
                * (noon_utc - date_file1).total_seconds()

        output_mapfile = \
            f"{self.site_abbrev}{date.strftime('%Y%m%d')}.map"
        output_mapfile = os.path.join(self.map_path, output_mapfile)

        # write header
        with open(mapfiles[0], "r") as f:
            header = f.readlines()[:12]
        self._check_mapfile_coordinates(header)
        with open(output_mapfile, "w") as f:
            for line in header:
                f.write(line)

        # write the rest of the file
        with open(output_mapfile, "a") as f:
            frw = fortranformat.FortranRecordWriter(
                "(2(f8.3,','),4(e10.3,','),1x,(f7.3,','),1x,(f7.3,','),"
                "(e10.3,','),1x,(f6.1,','),(f8.3,','),1x,(f6.4,','),1x,"
                "f5.3)")
            file1 = file1.transpose()
            for line in file1:
                f.write(frw.write(line) + "\n")

    def _check_mapfile_coordinates(self, header):
        """Check if the coordinates of the mapfile are consistent.
        Print a warning if not.

        params:
            header (list of lines): originating from a GGG20 mapfile
        """
        line = header[1]
        lat_map = float(line[3:5])
        if line[5] == "S":
            lat_map *= -1
        lon_map = float(line[7:10])
        if line[10] == "W":
            lon_map *= -1

        lat = self.coords["lat"]
        lon = self.coords["lon"]

        if round(lat, 0) != lat_map:
            self.logger.warning(
                f"The Latitude of the map file ({lat_map}) "
                f"does not match the Latitude given to PROFFASTpylot ({lat})!")
        if round(lon, 0) != lon_map:
            self.logger.warning(
                f"The Longitude of the map file ({lon_map}) "
                f"Does not match the Latitude given to PROFFASTpylot ({lon})!")

    def _tccon_mode_warning(self):
        """Print warning if TCCON mode is activated """
        self.logger.warning(
            "TCCON Mode is activated!\nThis will not work with standard"
            " EM27/SUN interferograms.\nOnly continue if this setting"
            " was choosen by purpose. Otherwise break the execution!")

    def _get_localtime_offset(self):
        """Return offset between measurement time and local time.

        utc_offset + localtime_offset = total offset beteen Localtime and UTC.
        and thus
        localtime_offset = total_localtime_utc_offset - utc_offset
        """
        tf = TimezoneFinder()
        local_tz_name = tf.timezone_at(
            lat=self.coords["lat"],
            lng=self.coords["lon"])
        local_tz = pytz.timezone(local_tz_name)
        # Allways use winter time
        date_winter = dt.strptime("2000-01-01", "%Y-%m-%d")
        localtime_utc_timedelta = local_tz.utcoffset(date_winter)
        localtime_utc_offset = localtime_utc_timedelta.total_seconds() / 3600
        localtime_offset = localtime_utc_offset - self.utc_offset
        return localtime_offset
