from enum import Enum

from report_builder.abs_report_builder import AbsReportBuilder
from report_builder.csv_generator import CsvReportBuilder
from report_builder.svg_generator import SvgReportBuilder

builders = Enum('md', 'csv')


def create_report_builder(type: builders) -> AbsReportBuilder:
    if type == 'md':
        return SvgReportBuilder()
    if type == 'md':
        return CsvReportBuilder()
    raise ValueError('There is no builder option for type {}'.format(type))
