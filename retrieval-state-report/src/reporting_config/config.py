import configparser


class Config:

    def __init__(self, directory: str):
        config = configparser.RawConfigParser()
        config.read(directory)
        self.upload_dir_location = config.get('data', 'upload_dir_location')
        self.archive_dir_location = config.get('data', 'archive_dir_location')
        self.ifg_pattern = config.get('data', 'ifg_pattern')
        self.reports_output = config.get('data', 'reports_output')
