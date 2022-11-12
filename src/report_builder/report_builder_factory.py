from enum import Enum

from report_builder.abs_report_builder import AbsReportBuilder
from report_builder.csv_builder import CsvReportBuilder
from report_builder.svg_builder import SvgReportBuilder

builders = Enum('md', 'csv')


def create_report_builder(chosen_type: builders, directory_name: str, file_name: str) -> AbsReportBuilder:
    if chosen_type == 'md':
        return SvgReportBuilder(directory_name, file_name)
    if chosen_type == 'csv':
        return CsvReportBuilder(directory_name, file_name)
    raise ValueError('There is no builder option for type {}'.format(type))
