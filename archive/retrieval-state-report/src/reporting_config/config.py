import json


class Config:
    def __init__(self, directory: str):
        with open("{}".format(directory), "r") as config_file:
            config_data = json.load(config_file)
            self.upload_dir_location = config_data["upload_dir_location"]
            self.archive_dir_location = config_data["archive_dir_location"]
            self.ifg_pattern = config_data["ifg_pattern"]
            self.reports_output = config_data["reports_output"]
