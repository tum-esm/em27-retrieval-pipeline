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
from prfpylot.prepare import Preparation


class FileMover(Preparation):
    """Copy, Move and remove temporary proffast Files."""

    def __init__(self, input_file, logginglevel="info"):
        super(FileMover, self).__init__(
            input_file,  logginglevel=logginglevel)
        # create all folders
        self.init_folders()

    def init_folders(self):
        """Create all relevant folders on startup if nonexistant.

        Check if relevant proffast folders are existant.
        Folders to be created:
        - pT, cal directories
        - result folder (backup of previous results)
        - logfiles
        """
        self._create_analysis_subdirs()
        self._create_result_dir()
        self._create_logfile_dir()

    def _create_analysis_subdirs(self):
        """Create subdirs of the analysis folder.

        Created folders:
            - 'cal' (for the spectra),
            - 'VMR-dim' (VMR-files),
            - pT
        """
        if os.path.exists(self.analysis_instrument_path):
            self.logger.warning(
                f"The analysis folder {self.analysis_instrument_path} "
                "exists already! "
                "The content may be overwritten.")

        # create folders 'YYMMDD/cal' and 'YYMMDD/VMR_dim'
        for date in self.dates:
            datestring = date.strftime("%y%m%d")
            # create cal-folder
            calfolder = os.path.join(
                self.analysis_instrument_path, datestring, "cal")
            if not os.path.exists(calfolder):
                os.makedirs(calfolder)
            # create VMR_dim folder:
            vmrfolder = os.path.join(
                self.analysis_instrument_path, datestring, "VMR_dim")
            if not os.path.exists(vmrfolder):
                os.makedirs(vmrfolder)
            self._create_pT_dir(date)

    def _create_pT_dir(self, date):
        """Create pt directory."""
        pt_path = os.path.join(
            self.analysis_instrument_path,
            date.strftime("%y%m%d"),
            "pT")
        if not os.path.exists(pt_path):
            os.makedirs(pt_path)

    def _create_result_dir(self):
        """Create a result dir and a backup if previous results exist.

        If the datafolder does exists, the existing folder is renamed adding
        backupX where X increases if an other backup does already exists.
        After renaming, a new folder is created.
        """

        # The result_foldername and result dir are already specified in
        # the init of prepare
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
                # rename and create new, empty folder
                os.rename(self.result_folder, result_folder_backup)
                os.makedirs(self.result_folder)
            else:  # backup_results is False
                self.logger.warning(
                    f"The result directory {self.result_folder} exists "
                    "already! The content may be overwritten."
                    )
        else:
            os.makedirs(self.result_folder)

    def move_results(self):
        """Move the results to the data folder.
        """
        suffix_list = [
            "colsens.dat",
            "colsens_?.dat",
            "invparms_?.dat",
            "job01_?.spc",
            "job02_?.spc",
            "job03_?.spc",
            "job04_?.spc",
            "job05_?.spc",
            "version_?.dat"
        ]
        source_folder = os.path.join(self.proffast_path, "out_fast")
        for date in self.dates:
            datestr = date.strftime("%y%m%d")
            prefix = self.site_name + datestr + "-"
            for suffix in suffix_list:
                file = prefix + suffix
                source = os.path.join(source_folder, file)
                sourcefiles = glob(source)
                for sfile in sourcefiles:
                    target = os.path.join(
                        self.result_folder,
                        os.path.basename(sfile))
                    try:
                        shutil.move(sfile, target)
                    except FileNotFoundError:
                        self.logger.error(f"File {sfile} was not found!")
                    except PermissionError:
                        self.logger.error(f"Could not write {target} due to "
                                          "permission issues.")
                    except OSError as e:
                        self.logger.error("Unknown error while movig file "
                                          f"{sfile}. Errormessage: {e}")

    def delete_pT_VMR_files(self):
        """Delete the pT and VMR files created by pcxs."""
        return  # added by Moritz Makowski
        wrk_fast_folder = os.path.join(self.proffast_path, "wrk_fast")
        for date in self.dates:
            pTFile =\
                f"{self.site_name}{date.strftime('%y%m%d')}-pT_fast_out.dat"
            VMRFile =\
                f"{self.site_name}{date.strftime('%y%m%d')}-VMR_fast_out.dat"
            for file in [pTFile, VMRFile]:
                try:
                    os.remove(os.path.join(wrk_fast_folder, file))
                except FileNotFoundError:
                    self.logger.error(
                        "File not Found: "
                        f"Could not delete {file}")

    def delete_abscos_files(self):
        """Delete the abscos.bin files created by pcxs."""
        wrk_fast_folder = os.path.join(self.proffast_path, "wrk_fast")
        for date in self.dates:
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
        # crate a folder in result dir for input files:
        inp_folder = os.path.join(self.result_folder, "input_files")
        if not os.path.exists(inp_folder):
            os.mkdir(inp_folder)
        for inp_file in self.global_inputfile_list:
            try:
                shutil.move(
                    inp_file,
                    os.path.join(inp_folder, os.path.basename(inp_file)))
            except FileNotFoundError:
                self.logger.error(
                    "File not found: "
                    f"Could not move {type} input file"
                    f" {inp_file}.")

    def _create_logfile_dir(self):
        """Create logfile dir if is does not exist."""
        if not os.path.exists(self.logfile_path):
            self.logger.debug(
                f"Logfile path did not exist, create {self.logfile_path}.")
            os.makedirs(self.logfile_path)
        self.logger.debug(f"Logfile_path: {self.logfile_path}")

    def _move_generallogfile_to_logdir(self):
        """Move the general logfile to the logdir"""

        # This have to be done at the end, since the folder is createt by the
        # program itself.
        for i, handler in enumerate(self.logger.handlers[:]):
            if i == 1:
                handler.close()
                self.logger.removeHandler(handler)
                del handler
            # self.logger.handlers[:][1].close()
        target = os.path.join(self.logfile_path,
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
