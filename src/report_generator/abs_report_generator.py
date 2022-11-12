from report_builder.abs_report_builder import AbsReportBuilder


class AbsReportGenerator:
    report_builder: AbsReportBuilder

    def __init__(self, builder: AbsReportBuilder):
        self.report_builder = builder

    def generate_report(self, filename: str):
        raise NotImplementedError('This is an abstract method. Consider rather invoking one of its inheritors.')

    @staticmethod
    def __get_dir_name(path):
        """
        Arguments:
        path (str):
            Full item path
        Returns:
        str:
            Get the folder preceding file
        """
        pass

    @staticmethod
    def __get_file_name(path):
        """
        Arguments:
        path (str):
            Full item path
        Returns:
        str:
            File name following the last slash
        """
        pass

    @staticmethod
    def __convert_date_to_numpy(date_as_string):
        """
        Arguments:
        date_as_string (str):
            Date as string in format yyyyMMdd
        Returns:
        numpy.datetime64:
            Date in numpy
        """
        pass
