"""Filemover is a module of PROFFASTpylot.

Move or copy the files created by PROFFAST during runtime.
Create relevant folders.

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

import os
from glob import glob
import shutil
import logging
from prfpylot.prepare import Preparation

class FileMover(Preparation):
    """Copy, Move and remove temporary proffast Files."""

    def __init__(
            self, input_file,
            logginglevel="info", external_logger=None, loggername=None):
        super(FileMover, self).__init__(
            input_file, logginglevel=logginglevel,
            external_logger=external_logger, loggername=loggername)
        # create all folders
        self.init_folders()
        # move the log file to the log-dir
        self._move_logfile()

    def init_folders(self):
        """Create all relevant folders on startup if nonexistant.

        Check if relevant proffast folders are existant.
        Folders to be created:
        - pT, cal directories
        - result folder (backup of previous results)
        - logfiles
        """
        self._create_analysis_cal_folders()
        self._create_result_dir()  # including the subdirs

    def _create_analysis_cal_folders(self):
        """Create the analysis and cal folder.

        Created folders:
            - analysis/<Site>_<Instrument>
            - analysis/<Site>_<Instrument>/<YYMMDD>/cal
                for the spectra of all measurement days.
        """
        if os.path.exists(self.analysis_instrument_path):
            self.logger.warning(
                f"The analysis folder {self.analysis_instrument_path} "
                "exists already! "
                "The content may be overwritten.")

        for date in self.meas_dates:
            datestring = date.strftime("%y%m%d")
            # create cal-folder
            calfolder = os.path.join(
                self.analysis_instrument_path, datestring, "cal")
            if not os.path.exists(calfolder):
                os.makedirs(calfolder)

    def _create_result_dir(self):
        """Create the result directories and a backup if previous results exist.

        Within this folder the following subfolders are created:
            - input_files, 
            - logfiles
            - raw_output_proffast

        Backup behavior:
            If backup_results is True and the result folder does exist:
            the existing folder is renamed adding
            backupX where X increases if an other backup does already exists.
            After renaming, a new folder is created.
        """

        # specification of self.result_folder in prepare
        if os.path.exists(self.result_folder):
            if self.backup_results is True:
                # check if already other backuped folder exist as well:
                backuped_results = glob(self.result_folder + "_backup*")
                # rename existing folder by adding _backupN where N is the N-th
                # backup
                result_folder_backup = self.result_folder\
                    + f"_backup{len(backuped_results)}"
                self.logger.warning(
                    f"The result directory {self.result_folder} exists "
                    "already! "
                    "Renamed existing one to "
                    f"{result_folder_backup} and created a new one.")
                os.rename(self.result_folder, result_folder_backup)

            else:  # backup_results is False
                self._create_result_subdirs()  # only if not existent
                self.logger.warning(
                    f"The result directory {self.result_folder} exists "
                    "already! The content may be overwritten. "
                    )
                return

        os.makedirs(self.result_folder)
        self._create_result_subdirs()

    def _create_result_subdirs(self):
        """Create the subfolders in the result folder.

        The folders 'input_files', 'logfiles' and 'raw_output_proffast' 
        are only created if not existent.
        """
        if not os.path.exists(self.input_files_folder):
            os.makedirs(self.input_files_folder)
        if not os.path.exists(self.raw_output_prf_folder):
            os.makedirs(self.raw_output_prf_folder)
        if not os.path.exists(self.logfile_folder):
            os.makedirs(self.logfile_folder)
        self.logger.debug("Created the subdirs in the result folder.")

    def move_results(self):
        """Move the gererated files to the result folder.

        The `invparms_?.dat`, `job_?.spc` and `version_?.dat` files
        are searched and moved to the result folder.
        If files are not found, a warning is printed.

        The colsens.dat are produced by PXCS and
            - moved if `delete_abscosbin_files` is True
            - copied if `delete_abscosbin_files` is False.

        This is to ensure that every run has them in the result folder,
        independent if pcxs was executed or skipped in this run.
        """

        suffix_list = [
            "invparms_?.dat",
            "job0?_?.spc",
            "version_?.dat"
        ]
        source_folder = os.path.join(self.proffast_path, "out_fast")

        # move/copy colsens files
        for local_date in self.local_dates:
            datestr = local_date.strftime("%y%m%d")
            prefix = self.site_name + datestr + "-"
            file = prefix + "colsens.dat"
            sfile = os.path.join(source_folder, file)
            target = os.path.join(self.raw_output_prf_folder, file)

            if self.delete_abscosbin_files: 
                action = "moved"
            else: 
                action = "copied"

            try:
                if self.delete_abscosbin_files:
                    shutil.move(sfile, target)
                else:
                    shutil.copy(sfile, target)
            except FileNotFoundError:
                self.logger.warning(
                    f"File {sfile} was not found in `prf/out_fast` "
                    f"and could not be {action} to "
                    "the result folder.\n"
                    "To solve this warning, try to delete "
                    "all *.abscos.bin files and rerun pcxs.")
            except PermissionError:
                self.logger.error(f"Could not write {target} due to "
                                  "permission issues.")
            except OSError as e:
                self.logger.error("OSError while moving file "
                                  f"{sfile}. Errormessage: {e}")

        # move invparms.dat .spc and version.dat
        for date in self.local_dates:
            datestr = date.strftime("%y%m%d")
            prefix = self.site_name + datestr + "-"
            for suffix in suffix_list:
                file = prefix + suffix
                source = os.path.join(source_folder, file)
                sourcefiles = glob(source)
                if len(sourcefiles) == 0:
                    self.logger.warning(
                        f"No file matchin the pattern {file} was not found!")

                for sfile in sourcefiles:
                    target = os.path.join(
                        self.raw_output_prf_folder,
                        os.path.basename(sfile))
                    try:
                        shutil.move(sfile, target)
                    except PermissionError:
                        self.logger.error(f"Could not write {target} due to "
                                          "permission issues.")
                    except OSError as e:
                        self.logger.error("OSError while movig file "
                                          f"{sfile}. Errormessage: {e}")

    def handle_pT_VMR_files(self):
        """Copy or move the pT and VMR files created by pcxs.

        If `delete-abscosbin_files` is True, the pT and VMR are MOVED to the
        result folder.
        If `delete-abscosbin_files` is False, the pT and VMR are COPIED to the
        result folder.

        They contain the prior information and are therefore an important part
        or the result. Hence, they are wanted to show up in the result folder
        in any case.
        """
        # Comment: This function could be handeld together with the
        # colsens files in move_results

        wrk_fast_folder = os.path.join(self.proffast_path, "wrk_fast")
        for date in self.local_dates:
            pTFile =\
                f"{self.site_name}{date.strftime('%y%m%d')}-pT_fast_out.dat"
            VMRFile =\
                f"{self.site_name}{date.strftime('%y%m%d')}-VMR_fast_out.dat"
            try:
                for file in [pTFile, VMRFile]:
                    filepath = os.path.join(wrk_fast_folder, file)
                    if self.delete_abscosbin_files:
                        action = "moved"
                        shutil.move(
                            filepath,
                            os.path.join(self.raw_output_prf_folder, file)
                            )
                    else:
                        action = "copied"
                        shutil.copy(
                            filepath,
                            os.path.join(self.raw_output_prf_folder, file)
                            )
            except FileNotFoundError:
                self.logger.warning(
                    f"File {file} was not found in `prf/wrk_fast` "
                    f"and could not be {action} to "
                    "the result folder.\n"
                    "To solve this warning, try to delete "
                    "all *.abscos.bin files and rerun pcxs.")

    def delete_abscos_files(self):
        """Delete the abscos.bin files created by pcxs."""
        wrk_fast_folder = os.path.join(self.proffast_path, "wrk_fast")
        for date in self.meas_dates:
            filename = f"{self.site_name}{date.strftime('%y%m%d')}-abscos.bin"
            try:
                os.remove(os.path.join(wrk_fast_folder, filename))
            except FileNotFoundError:
                self.logger.error(
                    "File not Found: "
                    f"Could not delete {filename}")

    def check_abscosbin_summed_size(self):
        """Get size of all abscos.bin files. Give warning if too large."""
        wrk_fast_folder = os.path.join(self.proffast_path, "wrk_fast")
        # the target folder doesnot exists, since this is an optional method
        abscosbinfiles = glob(
            os.path.join(wrk_fast_folder, "*-abscos.bin"))
        size = 0
        for file in abscosbinfiles:
            size += os.path.getsize(file)
        size = size / (1024 * 1024 * 1024)  # get size in GB, was in bytes
        self.logger.debug(f"Size of all abscosbin files: {size} GB.")
        if size > 100.:
            self.logger.warning("The size of all abscos bin files is "
                                + "{:6.2f} GB. ".format(size)
                                + "Please delete some to reduce disk usage!")

    def delete_input_files(self):
        """Delete the input files for preprocess, pcxs and inv"""
        for inp_file in self.global_inputfile_list:
            try:
                os.remove(inp_file)
            except FileNotFoundError:
                self.logger.error(
                    "File not Found: "
                    f"Could not remove {type} input file"
                    f" {inp_file}")

    def move_input_files(self):
        """Move the input files for prep., pcxs and inv to result folder"""

        for inp_file in self.global_inputfile_list:
            try:
                shutil.move(
                    inp_file,
                    os.path.join(
                        self.input_files_folder, os.path.basename(inp_file))
                    )
            except FileNotFoundError:
                self.logger.error(
                    "File not found: "
                    f"Could not move {type} input file"
                    f" {inp_file}.")

    def _move_logfile(self):
        """Move the logfile to the log-folder.
        
        For this it the file handler is closed, the file is moved and the 
        handler is re-opend.
        """
        # First get the correct handler. For this 
        for handler in self.logger.handlers:
            if handler.get_name() == "PRFpylotFileHandler":
                FHandler = handler

        new_logfile = os.path.join(
            self.logfile_folder, os.path.basename(self.global_log)
        )
        logging_level = FHandler.level
        PylotOnly = FHandler.filter
        FHandler.close()
        self.logger.removeHandler(FHandler)
        shutil.move(self.global_log, new_logfile)
        
        FHandler = logging.FileHandler(new_logfile, mode="a")
        FHandler.addFilter(PylotOnly)
        FHandler.setLevel(logging_level)
        FHandler.setFormatter(self.format_styles[self.logginglevel])
        self.logger.addHandler(FHandler)
        self.logger.debug("Logfile was moved and relinked to the logger")

    def _move_generallogfile_to_logdir(self):
        """Move the general logfile to the logdir.

        This needs to be done at the end, since the folder is created by the
        program itself."""

        for i, handler in enumerate(self.logger.handlers[:]):
            if i == 1:
                handler.close()
                self.logger.removeHandler(handler)
                del handler
            # self.logger.handlers[:][1].close()
        target = os.path.join(self.logfile_folder,
                              os.path.basename(self.pylot_log))
        try:
            shutil.move(self.pylot_log, target)
            self.logger.debug(
                "Moved the general logfile to the"
                " result/logfiles folder.")
        except (FileNotFoundError) as e:
            self.logger.debug(f"\nsource: {self.pylot_log} "
                              f"\ntarget: {target}")
            self.logger.debug(e)
            self.logger.error("Could not move logfile to new logfile dir! "
                              f"File is located in: {self.pylot_log}")

    def _move_prf_config_file(self):
        """Copy the PROFFASTpylot input file to the result folder."""
        self.logger.debug(
            "Copying the PROFFASTpylot input_file "
            f"{self.input_file} to {self.result_folder}")
        shutil.copy(self.input_file, self.result_folder)
