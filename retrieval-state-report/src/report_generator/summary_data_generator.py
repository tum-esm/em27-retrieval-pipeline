import glob
from typing import Dict, Union

import numpy
import pandas as pd

from src.reporting_config.config import Config

from src import util
from src.report_builder.csv_builder import CsvReportBuilder
from src.report_builder.svg_builder import SvgReportBuilder


class SummaryDataGenerator:

    report_builder: Union[CsvReportBuilder, SvgReportBuilder]

    def __init__(self, config: Config, report_name: str, report_type: str):
        self.report_name = report_name
        self.archive_dir_location = config.archive_dir_location
        self.upload_dir_location = config.upload_dir_location
        self.directory_name = config.reports_output
        self.ifg_pattern = config.ifg_pattern
        self.report_type = report_type
        self.__create_report_builder(report_type, self.directory_name, self.report_name)

    def __create_report_builder(
        self, report_type: str, directory_name: str, report_name: str
    ) -> None:
        if report_type == "md":
            self.report_builder = SvgReportBuilder(directory_name, report_name)
        elif report_type == "csv":
            self.report_builder = CsvReportBuilder(directory_name, report_name)

    def __map_days_to_ifgs(
        self, ifg_root_directory: str
    ) -> Dict[numpy.datetime64, int]:
        files = glob.glob(ifg_root_directory)
        day_to_count: Dict[numpy.datetime64, int] = {}
        for file in files:
            container_dir = util.get_dir_name(file)
            date_time_obj = util.convert_date_to_numpy(container_dir)
            if day_to_count.get(date_time_obj, None) is None:
                day_to_count[date_time_obj] = 0
            day_to_count[date_time_obj] += 1
        return day_to_count

    def __map_days_to_ifgs_in_archive(self) -> Dict[numpy.datetime64, int]:
        path = "{}/*/ifgs/{}".format(self.archive_dir_location, self.ifg_pattern)
        return self.__map_days_to_ifgs(path)

    def __map_days_to_ifgs_in_upload(self) -> Dict[numpy.datetime64, int]:
        path = "{}/*/*/{}".format(self.upload_dir_location, self.ifg_pattern)
        return self.__map_days_to_ifgs(path)

    def generate_report(self) -> None:
        if self.report_type == "csv":
            raise NotImplementedError("This operations is not supported")
        archive_map = self.__map_days_to_ifgs_in_archive()
        upload_map = self.__map_days_to_ifgs_in_upload()

        self.report_builder.create_output(
            "{}_archive".format(self.report_name), pd.Series(archive_map), "", ""
        )

        self.report_builder.create_output(
            "{}_upload".format(self.report_name), pd.Series(upload_map), "", ""
        )

        self.report_builder.save_file()
