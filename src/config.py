import configparser


class Config:

    def __init__(self, directory: str):
        config = configparser.RawConfigParser()
        config.read(directory)
        self.upload_dir_root = config.get('data', 'upload_dir_root')
        self.archive_root = config.get('data', 'archive_root')
