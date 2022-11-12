import pandas as pd


class AbsReportBuilder:

    def __init__(self, directory_name: str, file_name: str):
        self.file_name = file_name
        self.directory_name = directory_name
        pass

    def create_output(self, subreport_name: str, series: pd.Series):
        raise NotImplementedError('This is an abstract method. Consider rather invoking one of its inheritors.')

    def save_file(self):
        raise NotImplementedError('This is an abstract method. Consider rather invoking one of its inheritors.')
