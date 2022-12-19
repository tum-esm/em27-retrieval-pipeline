import configparser


class Config:

    def __init__(self, directory: str):
        config = configparser.RawConfigParser()
        config.read(directory)
        self.db_ip = config.get('db', 'ip')
        self.db_port = config.get('db', 'port')
        self.db_username = config.get('db', 'username')
        self.db_password = config.get('db', 'password')
        self.retrieval_version = config.get('db', 'retrieval_version')
        self.database_name = config.get('db', 'database_name')
        self.csv_locations = config.get('csv', 'csv_locations').split(',')
        self.cache_folder_location = config.get('csv', 'cache_folder_location')
