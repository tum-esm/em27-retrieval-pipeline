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
import datetime as dt
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
        "prep": "preprocess6",
        "inv": "invers25",
        "pcxs": "pcxs24"
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
        "mapfile_wetair_vmr": None,  # this is determined automatically if
                                     # you use mapfiles from tccon
        "coords": {"lat": None, "lon": None, "alt": None},
        "coord_file": None,
        "utc_offset": 0.0,
        "min_interferogram_size": 3.7,
        "start_with_spectra": False,
        "note": None,
        "delete_abscosbin_files": False,
        "delete_input_files": False,
        "delete_spc_files": True,
        "ils_parameters": None,
        "ignore_interpolation_error": None,
        "backup_results": True,
        "igram_pattern": "*.*",
        "instrument_parameters": "em27",
    }

    instrument_templates = {
        "em27": "em27.yml",
        "tccon_ka_hr": "tccon_ka_hr.yml",
        "tccon_ka_lr": "tccon_ka_lr.yml",
        "tccon_default_hr": "tccon_default_hr.yml",
        "tccon_default_lr": "tccon_default_lr.yml",
        "invenio": "invenio.yml",
        "vertex": "vertex.yml",
        "ircube": "ircube.yml"
    }

    def __init__(
            self, input_file, logginglevel="info",
            external_logger=None, loggername=None):
        """Initialize the PROFFASTpylot backbone.
        
        Params:
            input_file (str): The path to a yaml input file.
            logginglevel (str):
                A string specifying the logging level (`debug`, `info`,
                `warning`).
            external_logger (None):
                Optionally, an external logger can be given by providing an
                instance of an logging.logger class. Note that to this logger,
                the FileHandler and StreamHandler are added.
            loggername (None):
                Optionally, the name of the logger can be specified. This can be
                usefull to access the logger outside of the PROFFASTpylot.
                If loggername is None the default loggername is 'PROFFASTpylot'.
        """
        self.logger = self.create_logger(
            logginglevel=logginglevel,
            external_logger=external_logger, loggername=loggername)
        self.logger.info(
            "++++ Welcome to PROFFASTpylot ++++")
        self.logger.debug("Start reading input file...")

        # read input file
        with open(input_file, "r") as f:
            args = yaml.load(f, Loader=yaml.FullLoader)

        for option, value in args.items():
            self.__dict__[option] = value

        if args.get("start_with_spectra") is True:
            self.mandatory_options.remove("interferogram_path")
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

        # load instrument specific parameters:
        # try if a preset instrument parameter file is available:
        instrument_file = self.instrument_templates.get(
            self.instrument_parameters)
        if instrument_file is not None:
            # file is available. load path:
            instrument_file = os.path.join(
                self.prfpylot_path, "templates", "instrument_templates",
                instrument_file)
        else:
            # no match, load external file:
            instrument_file = self.instrument_parameters
        # now we can load the yaml file:
        try:
            with open(instrument_file, "r") as f:
                self.instrument_args = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            self.logger.error(
                f"The instrument file '{instrument_file}' could not be found"
                " on disk.\nPlease give a correct filename or use"
                " a pre-defined instrument template: "
                ", ".join(list(self.instrument_templates.keys())) + "\n."
                "This is a fatal error. Terminating PROFFASTpylot."
            )
            exit()
        # convert the Boolean values to "T" and "F"
        temp = self.instrument_args.copy()
        for key, val in temp.items():
            if isinstance(val, bool):
                if val:
                    self.instrument_args[key] = "T"
                else:
                    self.instrument_args[key] = "F"

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
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        if isinstance(start_date, str):
            start_date = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
        self.meas_dates = self.get_meas_dates(
                start_date=start_date,
                end_date=end_date
            )

        # make relative paths absolute
        paths = [
            "map_path", "pressure_path", "pressure_type_file",
            "interferogram_path", "analysis_path", "result_path",
            "analysis_instrument_path"]
        for path in paths:
            self.__dict__[path] = os.path.abspath(self.__dict__[path])

        # coordinates
        self.coords = self.get_coords()

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

        self.mapfile_format = None  # is determined in prepare_mapfile
        if self.mapfile_wetair_vmr is not None:
            self.logger.warning(
                "The parameter `mapfile_wetair_vmr` was given in the "
                "input file. Don't use this option if you are using ggg2020 "
                "or ggg2014 mapfiles from TCCON!")

        dt_format = "%y%m%d"
        result_foldername = "{}_{}_{}-{}".format(
            self.site_name,
            self.instrument_number,
            self.meas_dates[0].strftime(dt_format),
            self.meas_dates[-1].strftime(dt_format))
        self.result_folder = os.path.join(self.result_path, result_foldername)

        # path to the logfiles of the processes
        self.logfile_folder = os.path.join(
            self.result_folder, "logfiles")
        # path to store the input files in:
        self.input_files_folder = os.path.join(
            self.result_folder, "input_files")
        # path to store the final raw-outputfiles of proffast
        self.raw_output_prf_folder = os.path.join(
            self.result_folder, "raw_output_proffast")

        # calculate the _localtime_offset
        self._localtime_offset = self._get_localtime_offset()

        # initialise pressure handler
        self.pressure_handler = PressureHandler(
            self.pressure_type_file, self.pressure_path,
            self.meas_dates, self.logger, self.utc_offset)

        # collect all generated input files to move in FileMover
        self.global_inputfile_list = []

        self.logger.debug("Finished reading of input file.")

        # check and log if prepo., pcxs and invers were excuted:
        self.executed_preprocess = False
        self.executed_pcxs = False
        self.executed_invers = False

    def create_logger(
            self, logginglevel="info", loggername=None, external_logger=None):
        """Create and return a logger."""
        # check if the log_info is a string or an logger instance
        def test_log_level(level):
            return level in ["debug", "info", "warning"]
        assert test_log_level(logginglevel),\
            ("log_info must be one of the following:"
             f"`debug`, `info` or `warning`. Not {logginglevel}.")
        self.logginglevel = logginglevel
        num_level = {"debug": 10, "info": 20, "warning": 30}

        # Use the current datetime as a unique identifier
        self.startstrg_run = dt.datetime.now().strftime("%y%m%d%H%M%S%f")
        logger = logging.getLogger(self.startstrg_run)

        # create stream and file handlers:
        logfile_name = f"pylot_{self.startstrg_run}.log"
        self.global_log = os.path.join(os.getcwd(), logfile_name)
        FHandler = logging.FileHandler(logfile_name, mode='w')
        FHandler.set_name("PRFpylotFileHandler")
        StreamHandler = logging.StreamHandler()
        for handler in [FHandler, StreamHandler]:
            handler.setLevel(num_level[logginglevel])


        # The format of the logging
        self.format_styles = {
            "debug": logging.Formatter(
                "{asctime}, {levelname}({filename}): {message}", style="{"),
            "info": logging.Formatter(
                "{asctime}, {levelname}: {message}", style="{"),
            "warning": logging.Formatter(
                "{asctime}, {levelname}: {message}", style="{")
        }

        if external_logger is None:
            if loggername is None:
                loggername = self.startstrg_run
            logger = logging.getLogger(loggername)
            logger.setLevel(logging.DEBUG)
            for handler in [FHandler, StreamHandler]:
                logger.addHandler(handler)
                handler.setFormatter(self.format_styles[logginglevel])
        else:
            logger = external_logger
            logger.addHandler(FHandler)
            FHandler.setFormatter(self.format_styles[logginglevel])
            FHandler.setLevel(num_level(logginglevel))
            FHandler.addFilter(PylotOnly())
            logger.debug("Found external logger.")
        # set logging to debug to record everything in the first place
        StreamHandler = logging.StreamHandler()
        if external_logger is None:
            logger.debug(
                f"Initialized logger with datetime {self.startstrg_run}.")
        return logger

    def get_meas_dates(self, start_date=None, end_date=None):
        """
        Return a list of dates in measurement time for the site + instrument.

        Truncate the list if start_date and end_date are given.

        Parameters:
            start_date (dt.date): optional start date
            end_date (dt.date): optional end date
        """
        if self.start_with_spectra is False:
            self.logger.debug(
                "Searching for all interferogram folders ...")
            searched_filetype = "interferograms"
            datapath = os.path.join(self.interferogram_path, "*")
        elif self.start_with_spectra is True:
            self.logger.debug(
                "Searching for all spectra folders ...")
            searched_filetype = "spectra"
            datapath = os.path.join(self.analysis_instrument_path, "*")

        dates = self._create_datelist(datapath)
        if len(dates) == 0:
            self.logger.critical(
                f"No {searched_filetype} were found at "
                f"{datapath}!")
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
        self.logger.debug(f"start_date is {self.start_date}")
        self.logger.debug(f"end_date is {self.end_date}")

        self.logger.info(
            "Run information:\n"
            f"Retrieval for Instrument {self.instrument_number} "
            f"at {self.site_name} with time offset {self.utc_offset}.\n"
            "The following dates will be processed:\n"
            f"{print_date_str}.\n")

        return dates

    def get_coords(self):
        """Return dict of coords.

        If coords were not given or contain None for at least one coordinate,
        the coord_file will be read.
        If the coord_file was also not given, operation will be terminated.
        """
        coord_error = (
            "Give the coordinates in the input file or specify a "
            "coordinate file!"
            )
        coords = self.coords
        if None in coords.values():
            if self.coord_file is None:
                self.logger.critical(coord_error)
                sys.exit()
            coords = self.get_coords_from_file(self.meas_dates[0])
            # check for consistent coordinates in measurement period
            last_coords = self.get_coords_from_file(self.meas_dates[-1])
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
                date = dt.datetime.strptime(date_str, "%y%m%d")
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
            date_str = dt.datetime.strftime(date, "%y%m%d")
            filename = "".join(
                [self.template_types[template_type],
                    f"{self.site_name}_{date_str}.inp"]
            )
        elif template_type == "prep":
            folder_path = os.path.join(self.proffast_path, "preprocess")
            date_str = dt.datetime.strftime(date, "%y%m%d")
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

    def generate_preprocess_input(self, meas_date):
        """Fills the preprocess tempate file.

        Calls self.get_prep_parameters(meas_date)
        Parameters:
            meas_date (dt.datetime):
                the date in measurement time to be processed

        Return:
            prf_input_file (str, or None):
                If no igrams are found, return None, else the path to the
                input file
        """
        # the name of the input file to be generated
        prf_input_file = self.get_prf_input_path("prep", meas_date)

        if meas_date is not None:
            date_str = dt.datetime.strftime(meas_date, "%y%m%d")
        self.logger.debug(
            f"Generating preprocess inp file for {date_str}..")
        parameters = self.get_prep_parameters(meas_date)
        if parameters["igrams"] == "":
            return None
        self.replace_params_in_template(
            parameters, "prep", prf_input_file)
        self.global_inputfile_list.append(prf_input_file)
        return prf_input_file

    def generate_pcxs_input(self, local_date):
        """Fills the pcxs input file.

        Calls `get_pcxs_parameters` with local_date.

        Parameters:
            local_date (dt.datetime):
                the date in local time to be processed

        Returns:
            prf_input_file (str): Path to the input file.
        """
        # the name of the input file to be generated
        prf_input_file = self.get_prf_input_path("pcxs", local_date)

        date_str = dt.datetime.strftime(local_date, "%y%m%d")

        parameters = self.get_pcxs_parameters(local_date)
        self.logger.debug(
            f"Generating {self.template_types['pcxs']}"
            f" inp file for {date_str}..")

        self.replace_params_in_template(
            parameters, "pcxs", prf_input_file)
        self.global_inputfile_list.append(prf_input_file)
        return prf_input_file

    def generate_invers_input(self, local_date):
        """Fills the invers input file.

        Calls `get_inv_parameters` with the local date.

        Parameters:
            local_date (dt.datetime):
                the date in local time to be processed

        Returns:
            prf_input_files, skipped_spectra:
                - prf_input_files (list):
                    A list of paths to the input files.
                - skipped_spectra (list):
                    List containing all spectra skipped 
                    at this day, due to missing pressure values. 
                    This list is provided by `get_spectra_pT_input` called in 
                    `get_inv_parameters`.
        """
        # the name of the input file to be generated
        prf_input_file = self.get_prf_input_path("inv", local_date)
        date_str = dt.datetime.strftime(local_date, "%y%m%d")
        self.logger.debug(
            f"Generating {self.template_types['inv']}"
            f" inp file for {date_str}..")
        list_of_parameters, skipped_spectra =\
            self.get_inv_parameters(local_date)
        prf_input_files = []
        for parameters in list_of_parameters:
            if parameters is None:
                prf_input_files.append(None)
            else:
                suffix = parameters["SUFFIX"]
                prf_input_files.append(prf_input_file[:-4] + f"_{suffix}.inp")
                self.replace_params_in_template(
                    parameters, "inv", prf_input_files[-1])
        # safe inputfiles in global list to move/delete them later
        self.global_inputfile_list.extend(
            [x for x in prf_input_files if x is not None]
            )
        # return several input files hence do it already here:
        return prf_input_files, skipped_spectra

    def get_igrams(self, meas_date):
        """Search for interferograms on disk and return a list of files."""
        date_str = meas_date.strftime("%y%m%d")
        igrams = glob(os.path.join(
            self.interferogram_path, date_str,
            self.igram_pattern))

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
                f"at {meas_date.date()}.")

        if igrams == []:
            self.logger.debug(f"No suitable Interferogram at day {date_str} "
                              "found in get_igrams().")
        return igrams

    def get_spectra(self, meas_date):
        """Return list of spectra for a given date (in measurement time).

        Parameters:
            date (dt.datetime): in measurement time

        Returns:
            spectra (list):
                with full path to all spectra of measurement date
                ["path_to/YYMMDD_HHMMSSSN.BIN", ...]

        """
        datestring = meas_date.strftime("%y%m%d")
        # search cal-folder
        spectra_searchstr = os.path.join(
            self.analysis_instrument_path,
            datestring,
            "cal",
            "*SN.BIN")

        spectra = glob(spectra_searchstr)
        return sorted(spectra)

    def get_localdate_spectra(self):
        """Return dict linking all spectra to local dates.

        Returns:
            localdate_spectra (dict):
                containing the a list of full pathes to the spectra for each 
                local date in the format
                `{local_date: ["path/YYMMDD_HHMMSSSN.BIN", ...]}`
        """
        all_spectra = []
        for date in self.meas_dates:
            tmp_spectra = self.get_spectra(date)
            all_spectra.extend(tmp_spectra)
        all_spectra.sort()
        localdate_spectra = {}
        for spectrum in all_spectra:
            times = self.get_times_of(spectrum=spectrum)
            local_time = times["local_time"]
            local_date = local_time.date()
            if local_date in localdate_spectra.keys():
                localdate_spectra[local_date].append(spectrum)
            else:
                localdate_spectra[local_date] = [spectrum]
        return localdate_spectra

    def get_times_of(self, spectrum):
        """Read measurement time from filename, calculate local and utc time.
        Check if UTC time is consistent in the spectra header.

        Parameters:
            spectrum (str): full path to a spectrum

        Returns:
            times(dict):
                A dict with the following keys:
                    - meas_time (dt.datetime): time parsed from the filename
                    - local_time (dt.datetime): calculated local time
                    - utc_time (dt.datetime): read from spectra header
        """
        spectrum_name = os.path.basename(spectrum)
        meas_time = dt.datetime.strptime(spectrum_name, "%y%m%d_%H%M%SSN.BIN")
        local_time = meas_time + timedelta(hours=self._localtime_offset)

        # read UTC time from header
        with codecs.open(
                spectrum, "r", encoding="utf-8", errors="ignore") as f:
            header = f.readlines(1)[:24]
        UTh = float(header[13].strip())
        UT_date = header[12].strip()
        utc_time = dt.datetime.strptime(UT_date, "%y%m%d") + timedelta(
            hours=UTh)

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

        times = {
            "meas_time": meas_time,
            "local_time": local_time,
            "utc_time": utc_time            
        }
        return times

    def replace_params_in_template(
            self, parameters, template_type, prf_input_file):
        """Generate a site specific input file by using a template.

        Parameters:
            parameters (dict): Containing keys which match the variable
                names in the template file. They are replaced by the entries.
            template_type (str): Can be "prep", "pt", "inv" or "pcxc"
            prf_input_file (str): The filename of the input file

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

    def get_prep_parameters(self, meas_date):
        """Return Parameters to be replaced in the preprocess template.

        Parameters:
            meas_date (dt.datetime): date in measurement time

        Returns:
            parameters (dict):
                dict with parameters to fill the preporcess template.
        """
        if self.ils_parameters is not None:
            # the first priority is always the ILS params given in the the
            # general config file:
            ME1, PE1, ME2, PE2 = self.ils_parameters
            if self.instrument_parameters != "em27":
                self.logger.warning(
                    "Individual ILS Parameters are used,"
                    " the parameters are not "
                    "taken from the official COCCON ILS list!\n"
                    f"Used ILS Parameters: {self.ils_parameters}.")
        else:
            # ILS parameters NOT given in general input file.
            if self.instrument_parameters == "em27":
                # for the EM27 try to take it from the ILS List:
                self.logger.debug("Load ILS parameters from file.")
                ME1, PE1, ME2, PE2 = self.get_ils_from_file(meas_date)
            else:
                # for all other instruments use per default an ideal ILS
                # Due to the historically grown design of proffast
                # it is neccesar to use ME=0.983 and PE=0. This is "converted"
                # in invers to unity ILS:
                ME1 = ME2 = 0.983
                PE1 = PE2 = 0.0
                self.logger.info(
                    "Using unity ILS parameter for non-em27 instruments as "
                    "default. If you want to use different, specify it in the "
                    "general input file.")

        lat = self.coords["lat"]
        lon = self.coords["lon"]
        alt = self.coords["alt"]
        comment = (
            "This spectrum is generated using preprocess5, a part of "
            "PROFFAST controlled by PROFFASTpylot.")
        if self.note is not None:
            comment = " ".join([comment, self.note])

        # get all good igrams
        igrams = self.get_igrams(meas_date)
        igrams = "\n".join(igrams)
        # generate path to outputfolder for this date:
        datestring = meas_date.strftime("%y%m%d")
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
            'path_preprocess_log': self.logfile_folder,
            'filename_logfile': logfile,
            'path_spectra': outfolder,
            'mpow_fft': self.instrument_args["mpow_fft"],
            'semi_fov': self.instrument_args["semi_fov"],
            'dual_ifg_recording': self.instrument_args["dual_ifg_recording"],
            'swap_channels': self.instrument_args["swap_channels"],
            'use_analytical_phase':
                self.instrument_args["use_analytical_phase"],
            'band_selection': self.instrument_args["band_selection"],
                     }
        return parameters

    def get_pcxs_parameters(self, local_date):
        """Return parameters to fill the pcxs20.inp template.

        Parameters:
            local_date (dt.datetime): date in local time

        Returns:
            parameters (dict):
                dict containing the parameters to fill the pcxs template.
        """

        self.logger.debug("Create pcxs input parameters ...")

        lat = self.coords["lat"]
        lon = self.coords["lon"]
        alt = self.coords["alt"]
        # prepare map file path
        if self.mapfile_format == "ggg2020":
            local_noon_utc = self.get_local_noon_utc(local_date)
            map_file = os.path.join(
                self.result_folder,
                "interpolated_mapfiles",
                f"{self.site_abbrev}{local_noon_utc.strftime('%Y%m%d%H')}"
                "_Z.map"
                )

        elif self.mapfile_format == "ggg2014":
            map_file = os.path.join(
                self.map_path,
                f"{self.site_abbrev}{local_date.strftime('%Y%m%d')}.map"
            )
        parameters = {
            "ALT": alt,
            "LAT": lat,
            "LON": lon,
            "DATAPATH": self.analysis_instrument_path,
            "DATE": local_date.strftime("%y%m%d"),
            "SITE": self.site_name,
            "MAPPATH_WITH_MAPFILE": map_file
        }

        self._set_wet_vmr()  # set type of mapfile
        parameters["WET_VMR"] = self.mapfile_wetair_vmr
        if self.mapfile_wetair_vmr not in [True, False]:
            raise RuntimeError(
                "It was not determined if the mapfile "
                "is based on dry or wet air.")
        return parameters

    def get_inv_parameters(self, local_date):
        """Return parameters to fill the invers20.inp template.

        If spectra from two measurement days (i.e. different folders) belong
        to one local date, spectra_pT_input is a list with two elements,
        else, the it has one element.

        For each element in the spectra_pT_input list a dict containing the
        parameters for the input files is generated.

        The list of spectra belongig to one local date is sorted by the
        measurement date of the spectra which is determined by the function
        get_times_of(spectrum).

        Parameters:
            local_date (dt.datetime): date in local time

        Returns:
            parameters, skipped_spectra:
                - parameters (list): Contains one or two dict objects, 
                    depending if all spectra of the local date are stored in
                    the same YYMMDD folder.
                - skipped_spectra (list): List containing all spectra skipped 
                    at this day, due to missing pressure values. This list is
                    provided by `get_sepctra_pT_input`.
        """
        spectra_pT_input, skipped_spectra = \
            self.get_spectra_pT_input(local_date)
        spectra = self.localdate_spectra[local_date]

        # select one spectraum that reperents the correct measurement
        # date for each element in the spectra_pT_input list
        if len(spectra_pT_input) == 1:
            representative_spectra = [spectra[0]]
            charlist = ["a"]
        elif len(spectra_pT_input) == 2:
            representative_spectra = [spectra[0], spectra[-1]]
            charlist = ["b", "c"]
        else:
            raise NotImplementedError(
                "Define a representative spectrum if the return of "
                "get_spectra_pT_input of a date can contain more "
                "than two lists.")

        parameters = []
        for sub_pT_input, spectrum, suffix \
                in zip(spectra_pT_input, representative_spectra, charlist):
            times = self.get_times_of(spectrum)
            if len(sub_pT_input) == 0:
                # occurs if no pressure was found for all spectra
                temp_parameters = None
            else:
                temp_parameters = {
                    "DATAPATH": self.analysis_instrument_path,
                    "MEASUREMENT_DATE": times["meas_time"].strftime("%y%m%d"),
                    "LOCAL_DATE": times["local_time"].strftime("%y%m%d"),
                    "SITE": self.site_name,
                    "SUFFIX": suffix,
                    "SPECTRA_PT_INPUT": "\n".join(sub_pT_input)
                }
            parameters.append(temp_parameters)
        return parameters, skipped_spectra

    def get_spectra_pT_input(self, local_date):
        """Return invers formatted pT infos for given local date.

        If two measurement dates belong to one local date,
        spectra_pT_input contains two lists.
        The list is split based on the filename of the spectra,
        since the filename refers to measurement time.

        The string has the format `YYMMDD_HHMMSSSN.BIN, pressure, T_PBL`

        This function replaces the pt_intraday.inp file from older PROFFAST
        versions.
        Note that T_PBL is currently set to 0.0.

        Parameters:
            local_date (dt.datetime): Date in local time

        Returns:
            spectra_pT_input (list), skipped_spectra (list):
                - spectra_pT_input: List containing a list of strings with 
                    spectra and pT infos.
                - skipped_spectra (list): List containing all spectra skipped 
                    at this day, due to missing pressure values.
        """
        # in case of two measurement days in a local date list, split them up:
        spectra_list = self.localdate_spectra[local_date]
        spectra0 = []
        spectra1 = []
        first_spectrum_name = os.path.basename(spectra_list[0])
        first_date = dt.datetime.strptime(first_spectrum_name[:6], "%y%m%d")
        spectra0.append(spectra_list[0])
        # compare the dates from filename with first filename in the list
        for spectrum in spectra_list[1:]:
            spectrum_name = os.path.basename(spectrum)
            current_date = dt.datetime.strptime(spectrum_name[:6], "%y%m%d")
            if current_date != first_date:
                spectra1.append(spectrum)
            else:
                spectra0.append(spectrum)
        if len(spectra1) == 0:
            assert len(spectra_list) == len(spectra0)
            split_spectra_list = [spectra0]
        else:
            split_spectra_list = [spectra0, spectra1]
        
        # create a list of all spectra skipped at this LOCAL day
        skipped_spectra = []
        
        spectra_pT_input = []
        for sublist in split_spectra_list:
            temp_pT_input = []
            for spec in sublist:
                # get utc time of spectrum
                times = self.get_times_of(spec)
                utc_time = times["utc_time"]
                pressure_offset = timedelta(
                    hours=self.pressure_handler.utc_offset)
                pressure_time = utc_time + pressure_offset

                # get pressure from pressure record
                p = self.pressure_handler.get_pressure_at(pressure_time)
                if p == 0:
                    self.logger.debug(
                        f"For the spectrum {spec} no pressure record is "
                        "available. The reason can be found in the previous "
                        "message. "
                        "Hence, this spectrum is not going to be "
                        "processed.\n")
                    skipped_spectra.append(os.path.basename(spec))
                    continue
                temp_pT_input.append(f"{os.path.basename(spec)}, {p}, 0.0")
            spectra_pT_input.append(temp_pT_input)

        return spectra_pT_input, skipped_spectra

    def get_ils_from_file(self, date):
        """Read the ILS parameters form the given file.

        Parameters:
            date (dt.datetime): If multiple ILS Parameters are given in the
                list, get the newest ILS parameters, that are already valid
                at date.

        Returns:
            ils_parameters (tuple): MEChan1, PEChan1, MEChan2, PEChan2
        """
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
        start_date = dt.datetime.combine(start_date, dt.datetime.min.time())

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
        end_date = dt.datetime.combine(end_date, dt.datetime.min.time())

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

    def prepare_map_file(self, local_date):
        """Generate map file if GGG2020 map file are used.

        Parameters:
            local_date (dt.datetime): date in local time

        Returns:
            success (bool):
                True if map files were found and created
                False if no files were found.
        """
        # search for GGG2020 map files:
        # This includes files produced by ginput as well as from a running
        # ggg2020 evaluation
        srchstrg = f"{self.site_abbrev}*Z.map"
        mapfiles = glob(os.path.join(self.map_path, srchstrg))
        if len(mapfiles) != 0:
            self.logger.debug("Detected GGG2020 map files!")
            # GGG2020map files found!
            self.mapfile_format = "ggg2020"
            self.interpolate_map_files(local_date)
        else:
            srchstrg = f"{self.site_abbrev}{local_date.strftime('%Y%m%d')}.map"
            mapfiles = glob(os.path.join(self.map_path, srchstrg))
            if len(mapfiles) == 1:
                self.logger.warning(
                    "Detected GGG2014 map file, at day "
                    f"{local_date.strftime('%Y-%m-%d')}. This is not "
                    "recommended! "
                    "PROFFASTpylot is calibrated using GGG2020 map files, "
                    "please use GGG2014 only for comparison purposes!")
                self.mapfile_format = "ggg2014"
            else:
                self.logger.warning(
                    "No suitable map file found at "
                    f"{self.map_path} for {local_date.strftime('%Y-%m-%d')}.")
                return False
        return True

    def _set_wet_vmr(self):
        """Set self.mapfile_wet_vmr if not given in input file
        to set the %WET_VMR% parameter.
        - GGG2014 map files: dry air (False)
        - GGG2020 map files: wet air (True)
        value can be given separately in input file.
        """
        if self.mapfile_wetair_vmr is not None:
            return
        if self.mapfile_format == "ggg2020":
            self.mapfile_wetair_vmr = True
        elif self.mapfile_format == "ggg2014":
            self.mapfile_wetair_vmr = False
        else:
            raise RuntimeError(
                "The format of the mapfile was not determined."
                )

    def get_local_noon_utc(self, local_date):
        """Return local noon in utc.

        Local noon is referring to the 12:00 in the local time.
        Daylight saving time is not considered for this transformation.

        Parameters:
            local_date (dt.datetime):
                date in local time

        Returns:
            local_noon_utc: 12:00 in local time converted to UTC
        """
        local_noon = dt.datetime(
            year=local_date.year,
            month=local_date.month,
            day=local_date.day, hour=12)
        total_localtime_utc_offset = timedelta(
            hours=(self.utc_offset + self._localtime_offset))
        local_noon_utc = local_noon - total_localtime_utc_offset
        return local_noon_utc

    def get_mapfiles(self, local_noon_utc):
        """Return mapfiles of date and following date of the local noon in UTC.
        """

        search_str = (
            f"{self.site_abbrev}*{local_noon_utc.strftime('%Y%m%d')}*Z.map")
        mapfiles = glob(os.path.join(self.map_path, search_str))

        # add files of the following day
        # in case of interpolation between 21:00 and 00:00
        next_day = local_noon_utc + timedelta(hours=24)
        search_str = (
            f"{self.site_abbrev}_*_"
            f"{next_day.strftime('%Y%m%d')}*Z.map")
        mapfiles.extend(
             glob(os.path.join(self.map_path, search_str)))
        mapfiles.sort()
        return mapfiles

    def interpolate_map_files(self, local_date):
        """Interpolate GGG2020 map files.

        Generate a map file at 12:00 local time.
        This method is only called for mapfiles of type GGG2020.
        The mapfile is created in <result_folder>/interpolated_mapfiles

        with the following filename:
            "<site_abbrev><local_noon_utc>_Z.map"

        The folder interpolated_mapfiles is created in this function.

        Parameters:
            local_date (dt.datetime): datetime in local time
        """
        local_noon_utc = self.get_local_noon_utc(local_date)
        mapfiles = self.get_mapfiles(local_noon_utc)

        # find the correct map files: before and after the hour of noon_utc
        i_noon = None  # local noon between i_noon and i_noon-1
        noon_hour = local_noon_utc.hour
        for i, file in enumerate(mapfiles):
            hour_file = int(file[-7:-5])
            if hour_file > noon_hour:
                i_noon = i
                break
        if i_noon in [None, 0]:
            self.logger.critical(
                f"Could not calculate mapfile for {local_noon_utc} UTC "
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
        # difference between two file is always 3 hours
        tdiff = 3 * 60 * 60   # seconds
        # date of file 1 for the requested time diff
        date_file1 = dt.datetime.strptime(
                    os.path.basename(mapfiles[i_noon-1])[-15:-5], "%Y%m%d%H")
        for i in range(file1.shape[0]):
            # do a linear interpolation, calculate everything in seconds:
            file1[i, :] = file1[i, :] + (file2[i, :] - file1[i, :]) / tdiff \
                * (local_noon_utc - date_file1).total_seconds()

        output_folder = os.path.join(
            self.result_folder, "interpolated_mapfiles")
        os.makedirs(output_folder, exist_ok=True)

        output_filename = (
            f"{self.site_abbrev}"
            f"{local_noon_utc.strftime('%Y%m%d%H')}_Z.map"
            )

        output_mapfile = os.path.join(output_folder, output_filename)

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
                "(2(f8.3,','),4(e10.4,','),1x,(f7.3,','),1x,(f7.3,','),"
                "(e10.3,','),1x,(f6.1,','),(f8.3,','),1x,(f6.4,','),1x,"
                "f5.3)")
            file1 = file1.transpose()
            for line in file1:
                f.write(frw.write(line) + "\n")

    def _check_mapfile_coordinates(self, header):
        """Check if the coordinates of the mapfile are consistent.
        Print a warning if not.

        Parameters:
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
        date_winter = dt.datetime.strptime("2000-01-01", "%Y-%m-%d")
        localtime_utc_timedelta = local_tz.utcoffset(date_winter)
        localtime_utc_offset = localtime_utc_timedelta.total_seconds() / 3600
        localtime_offset = localtime_utc_offset - self.utc_offset
        return localtime_offset

class PylotOnly(logging.Filter):
    """
    A filter which filters out all logs not originating from the pylot.

    This is used when an external logger is provided, to prevent external
    logging messages to show up in the PROFFASTpylot custom log file.
    """
    filenames = ["prepare.py", "filemover.py", "pylot.py", "pressure.py"]

    def filter(self, record):
        if record.filename in self.filenames:
            return True
        else:
            return False
