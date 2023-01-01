from typing import Union, Dict, overload

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from mdutils.mdutils import MdUtils
from mdutils import Html
from datetime import datetime


class SvgReportBuilder:
    DAYS = ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."]
    MONTHS = [
        "Jan.",
        "Feb.",
        "Mär.",
        "Apr.",
        "Mai",
        "Juni",
        "Juli",
        "Aug.",
        "Sept.",
        "Okt.",
        "Nov.",
        "Dez.",
    ]

    md_file: MdUtils

    def __init__(self, directory_name: str, file_name: str):
        self.file_name = file_name
        self.directory_name = directory_name
        self.md_file = MdUtils(
            file_name="{}/{}".format(directory_name, file_name), title=file_name
        )

    @staticmethod
    def __plot_heatmap(
        series: pd.Series,
        start: pd.Series.dt = None,
        end: pd.Series.dt = None,
        mean: bool = False,
        ax: Union[mpl.axes.Axes, None] = None,
        **kwargs: str,
    ) -> mpl.axes.Axes:
        """Plot a calendar heatmap given a datetime series.

        Arguments:
            series (pd.Series):
                A series of numeric values with a datetime index. Values occurring
                on the same day are combined by sum.
            start (Any):
                The first day to be considered in the plot. The value can be
                anything accepted by :func:`pandas.to_datetime`. The default is the
                earliest date in the data.
            end (Any):
                The last day to be considered in the plot. The value can be
                anything accepted by :func:`pandas.to_datetime`. The default is the
                latest date in the data.
            mean (bool):
                Combine values occurring on the same day by mean instead of sum.
            ax (matplotlib.Axes or None):
                The axes on which to draw the heatmap. The default is the current
                axes in the :module:`~matplotlib.pyplot` API.
            **kwargs:
                Forwarded to :meth:`~matplotlib.Axes.pcolormesh` for drawing the
                heatmap.

        Returns:
            matplotlib.collections.Axes:
                The axes on which the heatmap was drawn. This is set as the current
                axes in the `~matplotlib.pyplot` API.
        """

        dates = series.index.floor("D")
        group = series.groupby(dates)
        series = group.mean() if mean else group.sum()

        start = pd.to_datetime(start or series.index.min())
        end = pd.to_datetime(end or series.index.max())

        end += np.timedelta64(1, "D")

        start_mon = start - np.timedelta64((start.dayofweek + 0) % 7, "D")
        end_mon = end + np.timedelta64(7 - end.dayofweek - 0, "D")

        num_weeks = (end_mon - start_mon).days // 7
        heatmap = np.zeros((7, num_weeks))
        ticks = {}
        for week in range(num_weeks):
            for day in range(7):
                date = start_mon + np.timedelta64(7 * week + day, "D")
                if date.day == 1:
                    ticks[week] = SvgReportBuilder.MONTHS[date.month - 1]
                if date.dayofyear == 1:
                    ticks[week] += f"\n{date.year}"
                if week == 0 and day == 0 and date.dayofyear != 1:
                    ticks[week] += f"\n{date.year}"
                if start <= date < end:
                    heatmap[day, week] = series.get(date, 0)

        y = np.arange(8) - 0.5
        x = np.arange(num_weeks + 1) - 0.5

        ax = ax or plt.gca()
        mesh = ax.pcolormesh(x, y, heatmap, **kwargs)
        ax.invert_yaxis()

        ax.set_xticks(list(ticks.keys()))
        ax.set_xticklabels(list(ticks.values()))
        ax.set_yticks(np.arange(7))
        ax.set_yticklabels(SvgReportBuilder.DAYS)

        plt.sca(ax)
        plt.sci(mesh)

        return ax

    def __generate_svg(self, subreport_name: str, series: pd.Series) -> None:
        figsize = plt.figaspect(7 / 56)
        fig = plt.figure(figsize=figsize)

        ax = SvgReportBuilder.__plot_heatmap(series, edgecolor="black")
        plt.colorbar(ticks=range(5), pad=0.02)

        cmap = mpl.cm.get_cmap("Reds", 5)
        plt.set_cmap(cmap)
        plt.clim(-0.5, 4.5)

        ax.set_aspect("equal")

        fig.savefig(
            "{}/{}.svg".format(self.directory_name, subreport_name),
            bbox_inches="tight",
            format="svg",
        )

        plt.close(fig)

    def create_output(
        self,
        series: pd.Series,
        subreport_name: str,
        sensor: str | None = None,
        status: str | None = None,
    ) -> None:
        if series.empty:
            self.__create_empty_output(subreport_name)
            return
        self.__generate_svg(subreport_name, series)

        self.md_file.new_header(1, "Subreport: {}".format(subreport_name))
        path = subreport_name

        self.md_file.new_paragraph(Html.image(path="{}.svg".format(path), size="300"))
        self.md_file.write("\n")

    def __create_empty_output(self, subreport_name: str) -> None:
        self.md_file.new_header(1, "Subreport: {}".format(subreport_name))
        self.md_file.new_paragraph("There is no data for this report")
        self.md_file.write("\n")

    def save_file(self) -> None:
        self.md_file.create_md_file()
