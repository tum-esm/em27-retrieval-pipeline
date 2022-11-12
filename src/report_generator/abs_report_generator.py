import os
from datetime import datetime

import numpy as np

from report_builder.abs_report_builder import AbsReportBuilder
from reporting_config.config import Config


class AbsReportGenerator:
    report_builder: AbsReportBuilder
    report_name: str
    directory_name: str
    ifg_pattern: str

    def __init__(self, config: Config, report_name: str):
        self.directory_name = config.reports_output
        self.report_name = report_name
        self.ifg_pattern = config.ifg_pattern

    def generate_report(self):
        raise NotImplementedError('This is an abstract method. Consider rather invoking one of its inheritors.')

    @staticmethod
    def get_dir_name(path):
        """
        Arguments:
        path (str):
            Full item path
        Returns:
        str:
            Get the folder, in which the file is stored
        """
        return os.path.basename(os.path.dirname(path))

    @staticmethod
    def get_file_name(path):
        """
        Arguments:
        path (str):
            Full item path
        Returns:
        str:
            File name following the last slash
        """
        return os.path.basename(path)

    @staticmethod
    def convert_date_to_numpy(date_as_string):
        """
        Arguments:
        date_as_string (str):
            Date as string in format yyyyMMdd
        Returns:
        numpy.datetime64:
            Date in numpy
        """
        return np.datetime64(datetime.strptime(date_as_string, "%Y%m%d").date())
