import glob
import os
from datetime import datetime

from pandas import DataFrame

from src.csv_processor import dictionary_columns

import pandas


class CacheProxy:
    __KEY_VALUE = 'df'

    def __init__(self, location):
        self.cache_files = []
        self.location = location

    @staticmethod
    def __map_filename_to_year(filename):
        try:
            return datetime.strptime(filename.partition('.h5')[0], '%Y').year
        except ValueError:
            print('Cache contains invalid keys: cannot convert {} to year'.format(filename))

    def __build_filename_from_year(self, year):
        return '{}/{}.h5'.format(self.location, year)

    def load_cache_in_memory_for(self, year):
        cached_data_frame = DataFrame(columns=list(dictionary_columns.values()))

        if os.path.isfile(self.__build_filename_from_year(year)):
            print('Cache for year {} found. Loading...'.format(year))
            cached_data_frame = pandas.read_hdf(self.__build_filename_from_year(year), key=self.__KEY_VALUE)
            print(cached_data_frame)
        return cached_data_frame

    def get_all_years_in_cache(self):
        if os.path.isdir(self.location):
            path = '{}/*.h5'.format(self.location)
            self.cache_files = glob.glob(path)
            if not self.cache_files:
                print('No cache file found')
                return []
            print('Cache files found. Loading...')
            years_in_cache = [self.__map_filename_to_year(filename.removeprefix(self.location + '/')) for filename in
                              self.cache_files]
            return years_in_cache
        print('The directory with supposed cache files does not exist')
        return []

    def refresh_contents(self, dataframe, key):
        print('Refreshing cache for year {}.'.format(key))

        dataframe.to_hdf(self.__build_filename_from_year(key), key=self.__KEY_VALUE, mode='w')

        print('Done refreshing cache.')

    def remove_for_year(self, year):
        os.remove(self.__build_filename_from_year(year))
