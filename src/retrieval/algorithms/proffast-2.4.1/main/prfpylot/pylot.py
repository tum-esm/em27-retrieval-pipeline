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
import codecs
from prfpylot.output.nc_cf_writer import NcWriter
from prfpylot.output.hdf_geoms_writer import GeomsGenWriter


class Pylot(FileMover):
    """Start all PROFFAST processes."""

    def __init__(
            self, input_file, logginglevel="info",
            external_logger=None, loggername=None):
        super(Pylot, self).__init__(
            input_file, logginglevel=logginglevel,
            external_logger=external_logger, loggername=loggername)
        self.logger.debug("Initialized the FileMover")

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

        # additionally generate netcdf output
        cf_writer = NcWriter(self.result_folder)
        cf_writer.write_nc()

        # additionally generate hdf output
        if self.geomsgen_inputfile is not None:
            geoms_out_path = os.path.join(
                self.result_folder, "output_hdf_geoms")
            geoms_writer = GeomsGenWriter(
                self.geomsgen_inputfile, geoms_out_path=geoms_out_path)
            geoms_writer.generate_geoms_files()

        self.logger.info(
            "The results of PROFFAST were written "
            f"to {self.result_folder}/ .")

    def run_preprocess(self, n_processes=1):
        """Main method to run preprocess."""
        if self.start_with_spectra is True:
            self.logger.info(
                "Running with option: 'start_with_spectra', "
                "skipping preprocessing. ...\n")
            return

        self.logger.info(
            f"Running preprocess with {n_processes} task(s) ...")

        # Create inputfiles. If None is returned no date was found for this
        # specific day
        all_inputfiles = []
        temp = self.meas_dates[:]
        for meas_date in temp:
            inputfile = self.generate_preprocess_input(meas_date)
            if inputfile is not None:
                all_inputfiles.append(inputfile)
            else:
                self.logger.warning(
                    f"No suitable iterferogram was found for day {meas_date}!"
                    "Skip processing of this day.")
                self.meas_dates.remove(meas_date)

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

        self.executed_preprocess = True
        self.logger.info("Finished preprocessing.\n")

    def run_pcxs(self, n_processes=1):
        """Run pcxs.

        Loops over local dates and executes the following steps:
            - check if the abscos bin file exists already.
            - Interpolate the mapfile.
              If no mapfile is found for a local date, the date is removed
              from self.local_dates.
            - generate the input file.
            - run pcxs(in parallel).

        Parameters:
            n_processes(int) = 1:
                If n_processes == 1, `run_pcxs_at` is called directly.
                Otherwise it is called via run_parallel.
        """
        self.executed_pcxs = True
        self.logger.info(f"Running pcxs with {n_processes} task(s) ...")
        output = []
        self.logger.debug("Get localdate spectra...")
        # define here, as needed several times later and costs computation time
        self.localdate_spectra = self.get_localdate_spectra()
        # create a list out of the dictionary to increase code clarity
        self.local_dates = list(self.localdate_spectra.keys())
        wrk_fast_path = os.path.join(self.proffast_path, "wrk_fast")

        # If we want to add the meassured p-value for PCXS we have to create
        # the pressure_df already now.
        if self.use_measured_pressure_for_pcxs:
            self.pressure_handler.prepare_pressure_df()

        inputfile_list = []
        temp = deepcopy(self.local_dates)
        for local_date in temp:
            # Check if absos file is there, skip
            srchstrg = (
                f"{self.site_name}{local_date.strftime('%y%m%d')}-abscos.bin")
            if os.path.exists(os.path.join(wrk_fast_path, srchstrg)):
                message = (
                    f"*.abscos.bin file for day {local_date} exists already."
                    " Skip calculation..")
                self.logger.info(message)
                output.append(
                    [message, "", "No return code", "No call String"])
                continue
            # Generate/find map files
            success = self.prepare_map_file(local_date)
            if not success:
                self.logger.warning(
                    f"Skip day {local_date} since no map file is present")
                self.local_dates.remove(local_date)
                continue
            # Generate input files:
            inputfile = self.generate_pcxs_input(local_date)
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

        Loops over localdates, generates the input files and runs invers.
        Execute write_ils_list.

        Parameters:
            n_processes(int) = 1:
                If n_processes == 1, `run_inv_at` is called directly.
                Otherwise it is called via run_parallel.
        """
        self.executed_invers = True
        self.logger.info(f"Running invers with {n_processes} task(s) ...")
        # needed if run_pcxs was not executed before
        if not hasattr(self, "local_dates"):
            self.localdate_spectra = self.get_localdate_spectra()
            self.local_dates = list(self.localdate_spectra.keys())

        output = []

        # The pressure_df is prepared already in PCXS when
        # the option `use_measured_pressure_for_pcxs` is selected.
        # When PCXS was not yet executed then prepare the df now::
        if (not self.executed_pcxs):
            # the interpolated pressure is stored and can be
            # accesed from self.pressure_handler
            self.pressure_handler.prepare_pressure_df()
        else:
            # apparently pcxs was executed. Check if the
            # `use_measured_pressure_for_pcxs` option is False, then create df
            if not self.use_measured_pressure_for_pcxs:
                self.pressure_handler.prepare_pressure_df()

        p_data_warnings = {}

        all_inputfiles = []
        temp_list = self.local_dates.copy()
        for local_date in temp_list:
            input_files, skipped_spectra = \
                self.generate_invers_input(local_date)
            no_pData = all([infile is None for infile in input_files])
            if no_pData:
                self.logger.debug(
                    f"For date {local_date} no auxiliary data was available"
                    ". Hence, this day is skipped."
                )
                p_data_warnings[local_date] = "All spectra of this local day!"
                self.local_dates.remove(local_date)
            else:
                if len(skipped_spectra) != 0:
                    p_data_warnings[local_date] = skipped_spectra
                for input_file in input_files:
                    if input_file is None:
                        # only a subset of the input file is none.
                        continue
                else:
                    all_inputfiles.append(input_file)
        if len(p_data_warnings) != 0:
            warn_strg = (
                "Due to missing auxiliary data the following spectra were "
                "skipped:")
            for date, status in p_data_warnings.items():
                datestr = date.strftime("%Y-%m-%d")
                if type(status) == str:
                    warn_strg += f"\n{datestr}: {status}"
                else:
                    warn_strg += f"\n{datestr}: {'; '.join(status)}"
            self.logger.info(warn_strg + "\n")

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

        self.logger.debug("Write ot ILS file.")
        self.write_ils_file()

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

    def _read_ils_from_spectrum(self, spectrum):
        """Open spectrum and return used ILS Parameters."""
        with codecs.open(
                spectrum, "r", encoding="utf-8", errors="ignore") as f:
            header = f.readlines(1)[:40]
        ils_str_list = header[34].strip().split(",")
        ils = [float(ils_str) for ils_str in ils_str_list]
        if len(ils) == 4:  # with second channel
            return ils  # ME1, PE1, ME1, PE1
        elif len(ils) == 2:
            return [*ils, *ils]  # no second channel, ME1 = ME2 and PE1 = PE2

    def write_ils_file(self):
        """Write file containing ILS parameters.

        Read all ILS parameters from the spectra file header.
        Check if the ILS parameters are equal for the processing period.
        """
        ils_dict = {
            "ME1": [],
            "PE1": [],
            "ME2": [],
            "PE2": []
        }

        local_dates = []
        for local_date, spectra in self.localdate_spectra.items():
            # read ils form header
            ils_params = self._read_ils_from_spectrum(spectra[0])
            for ils_param, key in zip(ils_params, ils_dict.keys()):
                ils_dict[key].append(ils_param)
            local_dates.append(local_date)

        ils_dict["LocalDate"] = local_dates
        df_ils = pd.DataFrame(ils_dict).set_index("LocalDate")

        ils_path = os.path.join(self.result_folder, "ils_list.csv")
        df_ils.to_csv(ils_path)
        return

    def combine_results(self):
        """Combine the generated result files and save as csv."""
        if not self.executed_invers:
            self.logger.warning(
                "The method `combine_results` was called but invers was not "
                "executed. Therefore `combine_results has nothing to do. "
                "Please do not execute this function without executing "
                "`run_invers`."
            )
            return
        self.logger.debug("Moving results to final output folder ...")
        self.move_results()
        df = self._get_merged_df()
        df = self._add_timezones_to(df)
        df = self._select_rename_cols(df)

        dt_format = "%y%m%d"
        resultfile = "comb_invparms_{}_{}_{}-{}.csv".format(
            self.site_name,
            self.instrument_number,
            self.meas_dates[0].strftime(dt_format),
            self.meas_dates[-1].strftime(dt_format)
        )
        combined_file = os.path.join(
            self.result_folder, resultfile)
        df["UTC"] = df["UTC"].apply(lambda x: x.strftime("%Y-%m-%d %X"))
        df["LocalTime"] = df["LocalTime"].apply(
            lambda x: x.strftime("%Y-%m-%d %X"))

        format_list = [
            "%s",  # UTC
            "%s",  # LocalTime
            "%12.5f",  # JulianDate
            "%6.0f",  # YYMMDD
            "%6.1f",  # UTtimeh
            "%s",  # spectrum
            "%5.2f",  # gndPmap
            "%5.2f",  # gndP
            "%5.2f",  # gndTmap
            "%5.2f",  # gndT
            "%7.5f",  # latdeg
            "%7.5f",  # londeg
            "%7.3f",  # altim
            "%4.2f",  # appSZA
            "%5.2f",  # azimuth
        ]

        len_remaining = len(df.keys()) - len(format_list)
        format_list.extend(["%.5e"]*len_remaining)

        header = ", ".join(df.columns)
        np.savetxt(
            combined_file, df.values,
            header=header,
            fmt=format_list,
            delimiter=', ',
            comments='')

    def clean_files(self):
        """After execution clean up the files not needed anymore"""
        self.logger.info("Removing temporary files ...")

        self.logger.debug("Handling pT and VMR files...")
        if self.executed_pcxs:
            self.handle_pT_VMR_files()

        # handling abscosbin
        if self.executed_pcxs:
            if self.delete_abscosbin_files:
                self.logger.debug("Deleting abscos.bin files ...")
                self.delete_abscos_files()
            else:
                self.logger.info(
                    "Keeping abscos.bin files ...\n"
                    "They are located in "
                    f"{os.path.join(self.proffast_path, 'wrk-fast')}.")
                self.check_abscosbin_summed_size()

        # handling input files
        if self.delete_input_files:
            self.logger.debug("Deleting input files ...")
            self.delete_input_files()
        else:
            self.logger.debug("Moving input files ...")
            self.move_input_files()

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

        file = os.path.join(self.logfile_folder, f"{program_name}_output.log")

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
            self.raw_output_prf_folder, f"{self.site_name}*-invparms_?.dat")
        invparms_filelist = sorted(glob(search_str))
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
            'job05_gas03': 'CO2_STR',
            'job06_gas06': 'CO',
            'job06_gas04': 'CH4_S5P'
        }
        df = df.rename(columns=rename)

        # reorder colums
        cols = df.columns.tolist()
        cols = cols[-2:] + cols[:-2]
        df = df[cols]

        return df

    def _get_executable(self, program):
        """Return PROFFAST executable of the given program part.

        Parameters:
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
