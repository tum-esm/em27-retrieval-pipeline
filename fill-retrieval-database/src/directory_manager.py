from typing import Dict, List

import pandas
from pandas import DataFrame

from src.csv_iterator import CsvIterator
from src.csv_processor import (
    build_data_frame_from,
    detect_all_years_in_dataframe,
    filter_dataframe,
)


class DirectoryManager:
    def __init__(self, directory_locations: List[str], retrieval_version: str):
        self.locations = directory_locations
        self.retrieval_version = retrieval_version

    def retrieve_mapping_years_to_files(self) -> Dict[int, List[str]]:
        print("Started scanning data")
        mapping: Dict[int, List[str]] = {}
        iterator = CsvIterator(self.locations)
        count = 1
        while iterator.has_next_file():
            if count % 100 == 0:
                print("Scanned {} files".format(count))
            next_file = iterator.read_next_file()
            df = build_data_frame_from(next_file, self.retrieval_version)
            all_years = detect_all_years_in_dataframe(df)
            for year in all_years:
                if mapping.get(year) is None:
                    mapping[year] = []
                mapping[year].append(next_file)
            count = count + 1
        print("Done scanning data")
        return mapping

    def get_dataframe_for_year(
        self, year: int, map_years_to_files: Dict[int, List[str]]
    ) -> DataFrame:
        print("Reading in main memory dataframe for year {}".format(year))
        dfs = []
        for file in map_years_to_files[year]:
            df = build_data_frame_from(file, self.retrieval_version)
            dfs.append(df)

        df = filter_dataframe(pandas.concat(dfs, ignore_index=True), year)
        print("Done reading for year {}, {} rows available".format(year, len(df.index)))
        return df
