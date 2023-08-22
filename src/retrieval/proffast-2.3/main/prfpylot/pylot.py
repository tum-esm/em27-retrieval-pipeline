"""Pylot is a module of PROFFASTpylot.

Steer all parts of PROFFASTpylot by initialising an instance of the
Pylot class and executing the different run methods.
See also in proffastpylot/doc for more inforamation about the usage.

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

from prfpylot.filemover import FileMover
import pandas as pd
from subprocess import Popen, PIPE
import os
import sys
from glob import glob
import multiprocessing
from timezonefinder import TimezoneFinder
import pytz
import numpy as np
from functools import partial
from copy import deepcopy


class Pylot(FileMover):
    """Start all PROFFAST processes."""

    def __init__(self, input_file, logginglevel="info"):
        super(Pylot, self).__init__(
            input_file, logginglevel=logginglevel)
        self.logger.debug('Initialized the FileMover')

        # a queue to save all days where all interferograms are bad
        self.bad_day_queue = multiprocessing.Manager().Queue()

    def run(self, n_processes=1):
        """Execute all processes of profast.

        Run preporcessing, pcxs, invers.
        The generated data is moved and merged in a result folder.
        """
        try:
            self.run_preprocess(n_processes=n_processes)
            self.run_pcxs(n_processes=n_processes)
            self.run_inv(n_processes=n_processes)
            self.combine_results()
        finally:
            self.clean_files()

    def run_preprocess(self, n_processes=1):
        """Main method to run preprocess."""
        if self.start_with_spectra is True:
            self.logger.info(
                "Running with option: 'start_with_spectra', "
                "skipping preprocessing. ...\n")
            return

        self.logger.info(
            f"Running preprocess with {n_processes} task(s) ...")
        # check if TCCON Mode is activated. If yes create the tccon input file
        if self.tccon_mode:
            self.logger.debug("...create tccon file...")
            self.generate_prf_input("tccon")
        else:
            # check if TCCON file is present by accident. If yes delete it
            tccon_file = self.get_prf_input_path("tccon")
            if os.path.exists(tccon_file):
                os.remove(tccon_file)
                self.logger.warning(
                    "Found TCCON file, which was not expected."
                    "Delete it for normal processing.")
        # Create inputfiles. If None is returned no date was found for this
        # specific day
        all_inputfiles = []
        temp = self.dates[:]
        for date in temp:
            inputfile = self.generate_prf_input("prep", date)
            if inputfile is not None:
                all_inputfiles.append(inputfile)
            else:
                self.logger.warning(
                    f"No suitable iterferogram was found for day {date}!"
                    "Skip processing of this day.")
                self.dates.remove(date)

        prep_exe = self._get_executable("prep")
        # store the path to change the cwd for the popen commmand
        exec_path = os.path.dirname(prep_exe)

        output = []
        if n_processes <= 1:
            for inputfile in all_inputfiles:
                tmp_out = self.run_prf_with_inputfile(
                    inputfile, prep_exe,
                    popen_kwargs={"cwd": exec_path})
                output.append(tmp_out)
        else:
            self.logger.debug("...start parallel processing...")
            subs_method = partial(
                self.run_prf_with_inputfile,
                executable=prep_exe,
                popen_kwargs={"cwd": exec_path}
            )
            pool = multiprocessing.Pool(processes=n_processes)
            output = pool.map(subs_method, all_inputfiles)
        self._write_logfile("preprocess", output)

        if self.tccon_mode:
            # delete tccon input file:
            os.remove(self.tccon_file)
            self.logger.debug("... delete TCCON file")
        self.logger.info("Finished preprocessing.\n")

    def run_pcxs(self, n_processes=1):
        """Run pcxs.
        If n_processes > 1, run_pcxs_at is
        called directly. Otherwise it is called via run_parallel
        """
        self.logger.info(f"Running pcxs with {n_processes} task(s) ...")
        output = []
        self.logger.debug("Get localdate spectra...")
        self.localdate_spectra = self.get_localdate_spectra()
        wrk_fast_path = os.path.join(self.proffast_path, "wrk_fast")
        inputfile_list = []
        temp = deepcopy(self.localdate_spectra)
        for date, spectra in temp.items():
            # Check if absos file is there, skip
            srchstrg = f"{self.site_name}{date.strftime('%y%m%d')}-abscos.bin"
            if os.path.exists(os.path.join(wrk_fast_path, srchstrg)):
                message = (
                    f"*.abscos.bin file for day {date} exists already."
                    " Skip calculation..")
                self.logger.info(message)
                output.append(
                    [message, "", "No return code", "No call String"])
                continue
            # Generate/find map files
            success = self.prepare_map_file(date)
            if not success:
                self.logger.warning(
                    f"Skip day {date} since no map file is present")
                self.localdate_spectra.pop(date)
                continue
            # Generate input files:
            inputfile = self.generate_prf_input("pcxs", date)
            inputfile_list.append(inputfile)

        pcxs_exe = self._get_executable("pcxs")
        # store the path to change the cwd for the popen commmand
        exec_path = os.path.dirname(pcxs_exe)

        if n_processes <= 1:
            for inputfile in inputfile_list:
                tmp_out = self.run_prf_with_inputfile(
                    inputfile, pcxs_exe, popen_kwargs={"cwd": exec_path})
                output.append(tmp_out)
        else:
            subs_method = partial(
                self.run_prf_with_inputfile,
                executable=pcxs_exe,
                popen_kwargs={"cwd": exec_path}
                )
            pool = multiprocessing.Pool(processes=n_processes)
            temp = pool.map(subs_method, inputfile_list)
            output.extend(temp)
        self._write_logfile("pcxs", output)
        self.logger.info("Finished pcxs.\n")

    def run_inv(self, n_processes=1):
        """Run inverse.
        If n_processes > 1, run_inv_at() is called directly.
        Otherwise it is called via run_parallel.
        """
        self.logger.info(f"Running invers with {n_processes} task(s) ...")
        if not hasattr(self, "localdate_spectra"):
            self.localdate_spectra = self.get_localdate_spectra()
        output = []

        # the interpolated pressure is stored and can be
        # accesed from self.pressure_handler
        self.pressure_handler.prepare_pressure_df()

        all_inputfiles = []
        for date, spectra in self.localdate_spectra.items():
            input_files = self.generate_prf_input("inv", date)
            all_inputfiles.extend(input_files)

        output = []
        inv_exe = self._get_executable("inv")
        # store the path to change the cwd for the popen commmand
        exec_path = os.path.dirname(inv_exe)

        if n_processes <= 1:
            for inputfile in all_inputfiles:
                tmp_out = self.run_prf_with_inputfile(
                    inputfile, inv_exe, popen_kwargs={"cwd": exec_path})
                output.append(tmp_out)
        else:
            subs_method = partial(
                self.run_prf_with_inputfile,
                executable=inv_exe,
                popen_kwargs={"cwd": exec_path})
            pool = multiprocessing.Pool(processes=n_processes)
            output = pool.map(subs_method, all_inputfiles)

        self._write_logfile("inv", output)
        self.logger.info("Finished invers.\n")

    def run_prf_with_inputfile(
            self, prf_inputfile, executable, popen_kwargs={}):
        """Run PROFFAST with the given inputfile"""
        prf_inputfile = os.path.basename(prf_inputfile)

        out, err, return_val = self._call_external_program(
            [executable, prf_inputfile], **popen_kwargs)

        outlist = \
            out, err, str(return_val),\
            " ".join([executable, prf_inputfile])
        return outlist

    def combine_results(self):
        """Combine the generated result files and save as csv."""
        self.logger.debug("Moving results to final output folder ...")
        self.move_results()

        df = self._get_merged_df()
        df = self._add_timezones_to(df)
        df = self._select_rename_cols(df)

        dt_format = "%y%m%d"
        resultfile = "comb_invparms_{}_{}_{}-{}.csv".format(
            self.site_name,
            self.instrument_number,
            self.dates[0].strftime(dt_format),
            self.dates[-1].strftime(dt_format)
        )
        combined_file = os.path.join(
            self.result_folder, resultfile)
        df["UTC"] = df["UTC"].apply(lambda x: x.strftime("%Y-%m-%d %X"))
        df["LocalTime"] = df["LocalTime"].apply(
            lambda x: x.strftime("%Y-%m-%d %X"))

        format_list = [
            "%s",  # UTC
            "%s",  # LocalTime
            "%s",  # spectrum
            "%12.5f",  # JulianDate
            "%6.1f",  # UTtimeh
            "%5.2f",  # gndP
            "%5.2f",  # gndT
            "%7.5f",  # latdeg
            "%7.5f",  # londeg
            "%7.3f",  # altim
            "%4.2f",  # appSZA
            "%5.2f",  # azimuth
            "%.5e",  # XH20
            "%.5e",  # XAIR
            "%.5e",  # XCO2
            "%.5e",  # XCH4
            "%.5e",  # XCO
            "%.5e",  # XCH4_S5P
            "%.5e",  # H20
            "%.5e",  # O2
            "%.5e",  # CO2
            "%.5e",  # CH4
            "%.5e",  # CO
            "%.5e"  # CH4_S5P
        ]

        header = ", ".join(df.columns)
        np.savetxt(
            combined_file, df.values,
            header=header,
            fmt=format_list,
            delimiter=', ',
            comments='')

        self.logger.info(
            "The combined results of PROFFAST were written "
            f"to {combined_file}.")

    def clean_files(self):
        """After execution clean up the files not needed anymore"""
        self.logger.info("Removing temporary files ...")

        # handling abscosbin
        if self.delete_abscosbin_files:
            self.logger.debug("Deleting abscos.bin files ...")
            self.delete_abscos_files()
            self.logger.debug("Deleting pT and VMR files...")
            self.delete_pT_VMR_files()
        else:
            self.logger.info(
                "Keeping abscos.bin files ...\n"
                "They are located in "
                f"{os.path.join(self.proffast_path, 'wrk-fast')}.")
            self.check_abscosbin_summed_size()
            self.logger.info(
                "Keeping pT and VMR files...\n"
                "They are located in "
                f"{os.path.join(self.proffast_path, 'wrk-fast')}.")

        # handling input files
        if self.delete_input_files:
            self.logger.debug("Deleting input files ...")
            self.delete_input_files()
        else:
            self.logger.debug("Moving input files ...")
            self.move_input_files()

        self._move_generallogfile_to_logdir()
        self._move_prf_config_file()
        self.logger.info("Done.\n")

    def _call_external_program(self, command_list, **kwargs):
        """Call a external program. Return output and error."""
        p = Popen(command_list, stdout=PIPE, stderr=PIPE, **kwargs)
        out, err = p.communicate()
        return_value = p.wait()
        out = out.decode("utf-8")
        err = err.decode("utf-8")
        return (out, err, return_value)

    def _write_logfile(self, program_name, output):
        """Write the output of preprocess, pcxs and inv to a logfile."""
        self.logger.debug(f"... Write logfile of {program_name} ...")

        file = os.path.join(self.logfile_path, f"{program_name}_output.log")

        logfile = open(file, "w")
        for i, entry in enumerate(output):
            out, err, return_code, call_strg = entry
            logfile.write(f"\n================= Task {i} ================\n")
            logfile.write(call_strg)
            logfile.write(f"\nReturn code: {return_code}\n")
            logfile.write("\nOutput:\n")
            logfile.write(out)
            logfile.write("\n\nErrors:\n")
            # Write error to logging, too
            if err != "":
                self.logger.error(f"Error when running {call_strg}:\n{err}")
            logfile.write(err)
            logfile.write("============================================\n")
            logfile.write("============================================\n\n\n")

        logfile.close()

    def _get_merged_df(self):
        """Read all invparm.dat files as Dataframe and combine them."""
        search_str = os.path.join(
            self.result_folder, f"{self.site_name}*-invparms_?.dat")
        invparms_filelist = glob(search_str)
        if len(invparms_filelist) == 0:
            raise RuntimeError(
                "Retrieval did not produce any *invparms*.dat files")

        df_list = [
            pd.read_csv(file, delimiter=",", skipinitialspace=True)
            for file in invparms_filelist]
        df = pd.concat(df_list)

        return df

    def _add_timezones_to(self, df):
        """Add UTC and local timezone at measurement location."""

        # drop columns with JulianDate == 0
        if 0. in df["JulianDate"].values:
            spectrumList = df["spectrum"].loc[df["JulianDate"] == 0]
            self.logger.warning(
                "The following spectra in invparm.dat where skipped since "
                "JulianDate equaled 0.0:\n" + "\n".join(spectrumList))
        df["JulianDate"] = df["JulianDate"].replace(0., np.nan)
        df.dropna(subset=["JulianDate"], inplace=True)

        df["UTC"] = pd.to_datetime(
            df["JulianDate"].values, origin="julian", unit="D", utc=True)

        tf = TimezoneFinder()
        local_tz_name = tf.timezone_at(
            lat=self.coords["lat"],
            lng=self.coords["lon"])
        local_tz = pytz.timezone(local_tz_name)
        df["LocalTime"] = df["UTC"].dt.tz_convert(local_tz)
        return df

    def _select_rename_cols(self, df):
        """Return df with selected and renamed columns."""
        rename = {
            'job01_gas01': 'H2O',
            'job02_gas07': 'O2',
            'job03_gas03': 'CO2',
            'job04_gas04': 'CH4',
            'job05_gas06': 'CO',
            'job05_gas04': 'CH4_S5P'
        }
        df = df.rename(columns=rename)

        sel_cols = [
            "UTC", "LocalTime", "spectrum",
            "JulianDate", "UTtimeh",
            "gndP", "gndT",
            "latdeg", "londeg", "altim",
            "appSZA", "azimuth",
            "XH2O", "XAIR",
            "XCO2", "XCH4",
            "XCO", "XCH4_S5P",
            "H2O", "O2",
            "CO2", "CH4",
            "CO", "CH4_S5P"
        ]
        df = df[[*sel_cols]]
        return df

    def _get_executable(self, program):
        """Return PROFFAST executable of the given program part.

        Params:
            program (str): can be "prep", "pcxs" and "inv"

        Returns:
            executable (str): depending on the current operating system.
        """
        if program == "prep":
            executable = os.path.join(self.proffast_path, "preprocess",
                                      self.template_types[program])
        else:
            executable = os.path.join(self.proffast_path,
                                      self.template_types[program])

        if sys.platform == "win32":
            executable += ".exe"
        return executable
