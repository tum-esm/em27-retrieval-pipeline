from datetime import datetime, timedelta
import os
from os.path import dirname
from typing import Iterator, Literal, Optional
from matplotlib import pyplot as plt
from contextlib import contextmanager
import matplotlib.dates as dates

PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


@contextmanager
def plot(
    subplot_row_count: int,
    subplot_col_count: int,
    subplot_number: int,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    title: Optional[str] = None,
    legend: Optional[
        Literal[
            "auto",
            "upper left",
            "upper right",
            "center left",
        ]
    ] = None,
    xaxis_scale: Literal["hours", "days", "months", "years"] = "years",
    plot_date_range: Optional[tuple[str, str]] = None,
) -> Iterator[plt.Axes]:
    axes = plt.subplot(subplot_row_count, subplot_col_count, subplot_number)

    axes.grid(True, which="major")
    axes.grid(True, which="minor", alpha=0.3)

    if xlabel is not None:
        axes.set_xlabel(xlabel)
    if ylabel is not None:
        axes.set_ylabel(ylabel)

    if title is not None:
        axes.set_title(title)

    yield axes

    if legend is not None:
        if legend == "auto":
            axes.legend()
        else:
            axes.legend(loc=legend)

    if xaxis_scale == "hours":
        axes.xaxis.set_minor_locator(dates.MinuteLocator(byminute=[0, 15, 30, 45]))
        axes.xaxis.set_major_locator(dates.HourLocator(byhour=range(0, 24, 2)))
        axes.xaxis.set_major_formatter(dates.DateFormatter("%H:%M"))

    if xaxis_scale == "days":
        axes.xaxis.set_minor_locator(dates.HourLocator())
        axes.xaxis.set_major_locator(dates.DayLocator())
        axes.xaxis.set_major_formatter(dates.DateFormatter("%Y-%m-%d"))

    elif xaxis_scale == "months":
        # every day
        axes.xaxis.set_minor_locator(dates.DayLocator())

        # every 14 days
        axes.xaxis.set_major_locator(dates.DayLocator(bymonthday=[1, 15]))
        axes.xaxis.set_major_formatter(dates.DateFormatter("%Y-%m-%d"))

    if xaxis_scale == "years":
        # every month
        axes.xaxis.set_minor_locator(dates.MonthLocator(bymonthday=1))

        # every 6 months
        axes.xaxis.set_major_locator(dates.MonthLocator(bymonth=[1, 7], bymonthday=1))
        axes.xaxis.set_major_formatter(dates.DateFormatter("%Y-%m-%d"))

    if plot_date_range is not None:
        axes.set_xlim(
            xmin=datetime.strptime(plot_date_range[0], "%Y%m%d")
            - timedelta(days=(7 if xaxis_scale == "months" else 31)),
            xmax=datetime.strptime(plot_date_range[1], "%Y%m%d")
            + timedelta(days=(7 if xaxis_scale == "months" else 31)),
        )

    # rotate x axis labels
    plt.setp(plt.xticks()[1], rotation=30)


def save_plot(filename: str) -> None:
    plt.savefig(
        os.path.join(PROJECT_DIR, "results", filename),
        dpi=300,
        bbox_inches="tight",
    )
