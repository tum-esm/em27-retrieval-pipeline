import glob
import os
import pandas
import pandas as pd

from report_builder.report_builder_factory import builders, create_report_builder
from report_generator.abs_report_generator import AbsReportGenerator
from reporting_config.config import Config


class StationDataGenerator(AbsReportGenerator):
    SUCCESSFUL = 'successful'
    FAILED = 'failed'

    df: pd.DataFrame
    report_type: builders

    def __init__(self, config: Config, report_name: str, report_type: builders):
        super().__init__(config, report_name)
        self.report_type = report_type
        self.archive_dir_location = config.archive_dir_location

    def __build_dataframe(self):
        versions = self.__get_versions()
        sensor_types = self.__get_sensor_types()
        archive_df = pd.DataFrame(columns=['sensor', 'version', 'status', 'date', 'count'])
        for sensor in sensor_types:
            for version in versions:
                for status in [self.SUCCESSFUL, self.FAILED]:
                    available_dates = glob.glob(
                        '{}/{}/{}/{}/*'.format(self.archive_dir_location, sensor, version, status))
                    for date in available_dates:
                        dir_name = AbsReportGenerator.get_file_name(date)
                        date_as_numpy = AbsReportGenerator.convert_date_to_numpy(dir_name)
                        count_in_date = len(glob.glob(
                            '{}/{}'.format(date, self.ifg_pattern)))
                        archive_df = pandas.concat([pd.DataFrame.from_dict({
                            'sensor': [sensor],
                            'version': [version],
                            'status': [status],
                            'date': [date_as_numpy],
                            'count': [count_in_date]
                        }), archive_df])

        self.df = archive_df

    def __get_versions(self):
        path = '{}/*/proffast-?.?-outputs'.format(self.archive_dir_location)
        return set([AbsReportGenerator.get_file_name(dir_name) for dir_name in glob.glob(path)])

    def __get_sensor_types(self):
        return set([os.path.basename(AbsReportGenerator.get_file_name(dir_name)) for dir_name in
                    glob.glob('{}/*'.format(self.archive_dir_location))])

    def __report_for_station_sensor(self, version, sensor, status) -> pd.Series:
        df = self.df
        return \
            df.loc[(df['version'] == version) & (df['sensor'] == sensor) & (df['status'] == status)].groupby(
                ['date'])[
                'count'].sum()

    def __report_all_stations(self, version: str, status: str) -> pd.Series:
        df = self.df
        return \
            df.loc[(df['version'] == version) & (df['status'] == status)].groupby(['date'])[
                'count'].sum()

    def generate_report(self):
        self.__build_dataframe()
        sensors = self.__get_sensor_types()
        versions = self.__get_versions()

        for version in sorted(versions):
            self.report_builder = create_report_builder(self.report_type, self.directory_name,
                                                        '{}_{}'.format(self.report_name, version))
            all_sensors_series_success = self.__report_all_stations(version, self.SUCCESSFUL)
            all_sensors_series_failure = self.__report_all_stations(version, self.FAILED)

            self.report_builder.create_output('{}_all_sensors_success'.format(version), all_sensors_series_success)
            self.report_builder.create_output('{}_all_sensors_failure'.format(version), all_sensors_series_failure)

            for sensor in sorted(sensors):
                one_sensor_series_success = self.__report_for_station_sensor(version, sensor, self.SUCCESSFUL)
                one_sensor_series_failure = self.__report_for_station_sensor(version, sensor, self.FAILED)

                self.report_builder.create_output('{}_sensor_{}_success'.format(version, sensor),
                                                  one_sensor_series_success)
                self.report_builder.create_output('{}_sensor_{}_failure'.format(version, sensor),
                                                  one_sensor_series_failure)

            self.report_builder.save_file()
