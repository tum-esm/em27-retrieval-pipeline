import glob
import os
import pandas
from datetime import datetime
from typing import List

from pandas import DataFrame
from src.csv_processor import dictionary_columns


class CacheProxy:
    __KEY_VALUE = 'df'
    cache_files: List[str]

    def __init__(self, location: str) -> None:
        self.cache_files = []
        self.location = location

    @staticmethod
    def __map_filename_to_year(filename: str) -> int:
        return datetime.strptime(filename.partition('.h5')[0], '%Y').year

    def __build_filename_from_year(self, year: int) -> str:
        return '{}/{}.h5'.format(self.location, year)

    def load_cache_in_memory_for(self, year: int) -> DataFrame:
        cached_data_frame = DataFrame(columns=list(dictionary_columns.values()))

        if os.path.isfile(self.__build_filename_from_year(year)):
            print('Cache for year {} found. Loading...'.format(year))
            cached_data_frame = pandas.read_hdf(self.__build_filename_from_year(year), key=self.__KEY_VALUE)
            print(cached_data_frame)
        return cached_data_frame

    def get_all_years_in_cache(self) -> List[int]:
        if os.path.isdir(self.location):
            path = '{}/*.h5'.format(self.location)
            self.cache_files = glob.glob(path)
            if not self.cache_files:
                print('No cache file found')
                return []
            print('Cache files found.')
            years_in_cache = [self.__map_filename_to_year(filename.removeprefix(self.location + '/')) for filename in
                              self.cache_files]
            return years_in_cache
        print('The directory with supposed cache files does not exist')
        return []

    def refresh_contents(self, dataframe: DataFrame, year: int) -> None:
        print('Refreshing cache for year {}.'.format(year))

        dataframe.to_hdf(self.__build_filename_from_year(year), key=self.__KEY_VALUE, mode='w')

        print('Done refreshing cache.')

    def remove_for_year(self, year: int) -> None:
        os.remove(self.__build_filename_from_year(year))
