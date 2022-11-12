import datetime
import glob
import os
import numpy as np
import pandas
import pandas as pd


class StationDataCollector:
    df: pd.DataFrame

    def __init__(self, archive_dir_location):
        self.archive_dir_location = archive_dir_location

    def print_dataframe(self):
        sensors = self._get_sensor_types()
        self.__build_dataframe()
        print(self.__report_all_stations('proffast-2.1-outputs'))

        for sensor in sensors:
            series = self.__report_for_station_sensor('proffast-2.1-outputs', sensor)
            # series = series.index[3].floor('D')
            print(series[0])
            print(series.index[0])

    def __report_all_stations(self, station: str) -> pd.DataFrame:
        df = self.df
        return df.loc[df['version'] == station].groupby(['version', 'status', 'date'])['count'].sum()

    def __build_dataframe(self):
        versions = self._get_versions()
        sensor_types = self._get_sensor_types()
        archive_df = pd.DataFrame(columns=['sensor', 'version', 'status', 'date', 'count'])
        for sensor in sensor_types:
            for version in versions:
                for status in ['successful', 'failed']:
                    available_dates = glob.glob(
                        '{}/{}/{}/{}/*'.format(self.archive_dir_location, sensor, version, status))
                    for date in available_dates:
                        dir_name = os.path.basename(os.path.basename(date))
                        date_as_numpy = np.datetime64(datetime.datetime.strptime(dir_name, "%Y%m%d").date())
                        count_in_date = len(glob.glob(
                            '{}/m?????????.ifg.????'.format(date)))
                        archive_df = pandas.concat([pd.DataFrame.from_dict({
                            'sensor': [sensor],
                            'version': [version],
                            'status': [status],
                            'date': [date_as_numpy],
                            'count': [count_in_date]
                        }), archive_df])

        self.df = archive_df

    def _get_versions(self):
        path = '{}/*/proffast-?.?-outputs'.format(self.archive_dir_location)
        return set([os.path.basename(os.path.basename(dir_name)) for dir_name in glob.glob(path)])

    def _get_sensor_types(self):
        return set([os.path.basename(os.path.basename(dir_name)) for dir_name in
                    glob.glob('{}/*'.format(self.archive_dir_location))])

    def __get_dir_name(self):
        pass

    def __convert_date_to_numpy(self):
        pass

    def __report_for_station_sensor(self, version, sensor) -> pd.DataFrame:
        df = self.df
        return \
            df.loc[(df['version'] == version) & (df['sensor'] == sensor)].groupby(
                ['version', 'sensor', 'date', 'status'])[
                'count'].sum()
