from src.config import Config
from src.report_generator.upload_dir_data_collector import UploadDirDataCollector
from src.report_generator.station_data_generator import StationDataCollector
from src.report_builder.svg_generator import date_heatmap
import pandas as pd

if __name__ == '__main__':
    config = Config('./config/config.properties')
    StationDataCollector(config.archive_root).print_dataframe()
