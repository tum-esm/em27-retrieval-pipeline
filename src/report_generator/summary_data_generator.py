import datetime
import glob
import os
import numpy as np

from report_builder.abs_report_builder import AbsReportBuilder
from report_generator.abs_report_generator import AbsReportGenerator


class ArchiveDataCollector(AbsReportGenerator):

    def __init__(self, builder: AbsReportBuilder, archive_dir_location: str):
        super().__init__(builder)
        self.archive_dir_location = archive_dir_location

    def __map_ifg_in_archive_to_day(self):
        path = '{}/*/ifgs/m?????????.ifg.????'.format(self.archive_dir_location)
        files = glob.glob(path)
        day_to_count = {}
        for file in files:
            container_dir = os.path.basename(os.path.dirname(file))
            date_time_obj = np.datetime64(datetime.datetime.strptime(container_dir, "%Y%m%d").date())
            if day_to_count.get(date_time_obj, None) is None:
                day_to_count[date_time_obj] = 0
            day_to_count[date_time_obj] += 1
        return day_to_count

    def __map_ifg_in_upload_to_day(self):
        path = '{}/*/*/m?????????.ifg.????'.format(self.upload_dir_location)
        files = glob.glob(path)
        day_to_count = {}
        for file in files:
            container_dir = os.path.basename(os.path.dirname(file))
            date_time_obj = np.datetime64(datetime.datetime.strptime(container_dir, "%Y%m%d").date())
            if day_to_count.get(date_time_obj, None) is None:
                day_to_count[date_time_obj] = 0
            day_to_count[date_time_obj] += 1
        return day_to_count

    def generate_report(self, filename: str):
        pass

