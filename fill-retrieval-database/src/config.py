import json


class Config:
    def __init__(self, directory: str):
        with open(directory, "r") as f:
            config = json.load(f)

        self.db_ip = config["ip"]
        self.db_port = config["port"]
        self.db_username = config["username"]
        self.db_password = config["password"]
        self.retrieval_version = config["retrieval_version"]
        self.database_name = config["database_name"]
        self.csv_locations = config["csv_locations"]
        self.cache_folder_location = config["cache_folder_location"]
