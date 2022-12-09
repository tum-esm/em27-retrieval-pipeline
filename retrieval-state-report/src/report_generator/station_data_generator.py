import glob
import os
from typing import List, Set, Union

import pandas
import pandas as pd

from src.reporting_config.config import Config

from src import util
from src.report_builder.csv_builder import CsvReportBuilder
from src.report_builder.svg_builder import SvgReportBuilder


class StationDataGenerator:
    SUCCESSFUL = "successful"
    FAILED = "failed"

    archive_df: pd.DataFrame
    upload_df: pd.DataFrame
    report_builder: Union[SvgReportBuilder, CsvReportBuilder]

    def __init__(self, config: Config, report_name: str, report_type: str):
        self.report_type = report_type
        self.archive_dir_location = config.archive_dir_location
        self.upload_dir_location = config.upload_dir_location
        self.directory_name = config.reports_output
        self.ifg_pattern = config.ifg_pattern
        self.report_name = report_name

    def __create_report_builder(
        self, report_type: str, directory_name: str, report_name: str
    ) -> None:
        if report_type == "md":
            self.report_builder = SvgReportBuilder(directory_name, report_name)
        elif report_type == "csv":
            self.report_builder = CsvReportBuilder(directory_name, report_name)

    def __build_dataframe_for_archive(self) -> None:
        versions = self.__get_versions_for_archive()
        sensor_types = self.__get_sensor_types_for_archive()
        archive_df = pd.DataFrame(
            columns=["sensor", "version", "status", "date", "count"]
        )
        for sensor in sensor_types:
            for version in versions:
                for status in [self.SUCCESSFUL, self.FAILED]:
                    available_dates = glob.glob(
                        "{}/{}/{}/{}/*".format(
                            self.archive_dir_location, sensor, version, status
                        )
                    )
                    for date in available_dates:
                        dir_name = util.get_file_name(date)
                        date_as_numpy = util.convert_date_to_numpy(dir_name)
                        count_in_date = len(
                            glob.glob("{}/{}".format(date, self.ifg_pattern))
                        )
                        archive_df = pandas.concat(
                            [
                                pd.DataFrame.from_dict(
                                    {
                                        "sensor": [sensor],
                                        "version": [version],
                                        "status": [status],
                                        "date": [date_as_numpy],
                                        "count": [count_in_date],
                                    }
                                ),
                                archive_df,
                            ]
                        )

        self.archive_df = archive_df

    def __build_dataframe_for_upload(self) -> None:
        sensor_types = self.__get_sensor_types_for_upload()
        upload_df = pd.DataFrame(columns=["sensor", "date", "count"])
        for sensor in sensor_types:
            available_dates = glob.glob(
                "{}/{}/*".format(self.upload_dir_location, sensor)
            )
            for date in available_dates:
                dir_name = util.get_file_name(date)
                date_as_numpy = util.convert_date_to_numpy(dir_name)
                count_in_date = len(glob.glob("{}/{}".format(date, self.ifg_pattern)))
                upload_df = pandas.concat(
                    [
                        pd.DataFrame.from_dict(
                            {
                                "sensor": [sensor],
                                "date": [date_as_numpy],
                                "count": [count_in_date],
                            }
                        ),
                        upload_df,
                    ]
                )

        self.upload_df = upload_df

    def __get_versions_for_archive(self) -> Set[str]:
        path = "{}/*/proffast-?.?-outputs".format(self.archive_dir_location)
        return set([util.get_file_name(dir_name) for dir_name in glob.glob(path)])

    def __get_sensor_types_for_archive(self) -> Set[str]:
        return set(
            [
                os.path.basename(util.get_file_name(dir_name))
                for dir_name in glob.glob("{}/*".format(self.archive_dir_location))
            ]
        )

    def __get_sensor_types_for_upload(self) -> Set[str]:
        return set(
            [
                os.path.basename(util.get_file_name(dir_name))
                for dir_name in glob.glob("{}/*".format(self.upload_dir_location))
            ]
        )

    def __report_for_station_sensor_for_archive(
        self, version: str, sensor: str, status: str
    ) -> pd.Series:
        df = self.archive_df
        return (
            df.loc[
                (df["version"] == version)
                & (df["sensor"] == sensor)
                & (df["status"] == status)
            ]
            .groupby(["date"])["count"]
            .sum()
        )

    def __report_for_station_sensor_for_upload(self, sensor: str) -> pd.Series:
        df = self.upload_df
        return df.loc[(df["sensor"] == sensor)].groupby(["date"])["count"].sum()

    def __report_all_stations_for_archive(self, version: str, status: str) -> pd.Series:
        df = self.archive_df
        return (
            df.loc[(df["version"] == version) & (df["status"] == status)]
            .groupby(["date"])["count"]
            .sum()
        )

    def generate_report(self) -> None:
        self.__build_dataframe_for_archive()
        sensors_archive = self.__get_sensor_types_for_archive()
        versions = self.__get_versions_for_archive()

        for version in sorted(versions):
            self.__create_report_builder(
                self.report_type,
                self.directory_name,
                "{}_{}".format(self.report_name, version),
            )
            all_sensors_series_success = self.__report_all_stations_for_archive(
                version, self.SUCCESSFUL
            )
            all_sensors_series_failure = self.__report_all_stations_for_archive(
                version, self.FAILED
            )

            if self.report_type == "md":
                self.report_builder.create_output(
                    "{}_all_sensors_success".format(version),
                    all_sensors_series_success,
                    "",
                    "",
                )
                self.report_builder.create_output(
                    "{}_all_sensors_failure".format(version),
                    all_sensors_series_failure,
                    "",
                    "",
                )

            for sensor in sorted(sensors_archive):
                one_sensor_series_success = (
                    self.__report_for_station_sensor_for_archive(
                        version, sensor, self.SUCCESSFUL
                    )
                )
                one_sensor_series_failure = (
                    self.__report_for_station_sensor_for_archive(
                        version, sensor, self.FAILED
                    )
                )

                self.report_builder.create_output(
                    "{}_sensor_{}_success".format(version, sensor),
                    one_sensor_series_success,
                    sensor,
                    self.SUCCESSFUL,
                )
                self.report_builder.create_output(
                    "{}_sensor_{}_failure".format(version, sensor),
                    one_sensor_series_failure,
                    sensor,
                    self.FAILED,
                )

            self.report_builder.save_file()

        self.__create_report_builder(
            self.report_type, self.directory_name, "{}".format("upload")
        )

        if self.report_type == "md":
            return

        self.__build_dataframe_for_upload()
        sensors_upload = self.__get_sensor_types_for_upload()
        for sensor in sorted(sensors_upload):
            self.report_builder.create_output(
                "upload",
                self.__report_for_station_sensor_for_upload(sensor),
                sensor,
                "",
            )
        self.report_builder.save_file()
