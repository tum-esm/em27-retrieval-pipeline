from pandas import DataFrame
from src.csv_processor import dictionary_columns, detect_new, detect_modified, detect_deleted
from src.cache_manager import CacheProxy
from src.config import Config
from src.directory_manager import DirectoryManager
from src.sql_manager import SqlManager


def process_measurements(properties):
    cache_proxy = CacheProxy(properties.cache_folder_location)
    directory_manager = DirectoryManager(properties.csv_locations, properties.retrieval_version)
    sql_manager = SqlManager(properties)

    all_years_in_cache = cache_proxy.get_all_years_in_cache()

    all_years_in_files = directory_manager.retrieve_mapping_years_to_files()

    for year in all_years_in_files:
        df = directory_manager.get_dataframe_for_year(year, all_years_in_files)
        cached_data_frame = DataFrame(columns=list(dictionary_columns.values()))
        if year in all_years_in_cache:
            print('Reading cache dataframe for year {}'.format(year))
            cached_data_frame = cache_proxy.load_cache_in_memory_for(year)
        new_rows = detect_new(df, cached_data_frame)
        sql_manager.insert_from_df(new_rows)
        modified_rows = detect_modified(df, cached_data_frame, new_rows)
        sql_manager.update_dataframe(modified_rows)
        deleted_rows = detect_deleted(df, cached_data_frame)
        sql_manager.delete_rows(deleted_rows)
        cache_proxy.refresh_contents(df, year)

        if year in all_years_in_cache:
            all_years_in_cache.remove(year)

    if all_years_in_cache:
        print('There is still obsolete data in cache, cleaning...')
        for year in all_years_in_cache:
            cache_proxy.remove_for_year(year)

        print('Ready...')

    return


def init_db(properties):
    SqlManager(properties).init_db()


if __name__ == '__main__':

    settings = Config('./config/config.properties')

    option = input('Do you want to create a database(1) or process csv files(2)?\n')
    if option == '1':
        init_db(settings)
    elif option == '2':
        process_measurements(settings)
