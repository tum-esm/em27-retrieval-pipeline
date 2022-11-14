import datetime
import glob
import os
from typing import Dict

import numpy
import numpy as np
import pandas as pd

from report_builder.report_builder_factory import create_report_builder
from reporting_config.config import Config
from report_generator.abs_report_generator import AbsReportGenerator


class SummaryDataGenerator(AbsReportGenerator):

    def __init__(self, config: Config, report_name: str, report_type: str):
        super().__init__(config, report_name)
        self.archive_dir_location = config.archive_dir_location
        self.upload_dir_location = config.upload_dir_location
        self.report_builder = create_report_builder(report_type, self.directory_name, self.report_name)

    def __map_days_to_ifgs(self, ifg_root_directory: str) -> Dict[numpy.datetime64, int]:
        files = glob.glob(ifg_root_directory)
        day_to_count: Dict[numpy.datetime64, int] = {}
        for file in files:
            container_dir = AbsReportGenerator.get_dir_name(file)
            date_time_obj = AbsReportGenerator.convert_date_to_numpy(container_dir)
            if day_to_count.get(date_time_obj, None) is None:
                day_to_count[date_time_obj] = 0
            day_to_count[date_time_obj] += 1
        return day_to_count

    def __map_days_to_ifgs_in_archive(self) -> Dict[numpy.datetime64, int]:
        path = '{}/*/ifgs/{}'.format(self.archive_dir_location, self.ifg_pattern)
        return self.__map_days_to_ifgs(path)

    def __map_days_to_ifgs_in_upload(self) -> Dict[numpy.datetime64, int]:
        path = '{}/*/*/{}'.format(self.upload_dir_location, self.ifg_pattern)
        return self.__map_days_to_ifgs(path)

    def generate_report(self):
        archive_map = self.__map_days_to_ifgs_in_archive()
        upload_map = self.__map_days_to_ifgs_in_upload()

        self.report_builder.create_output('{}_archive'.format(self.report_name),
                                          pd.Series(archive_map))

        self.report_builder.create_output('{}_upload'.format(self.report_name),
                                          pd.Series(upload_map))

        self.report_builder.save_file()
