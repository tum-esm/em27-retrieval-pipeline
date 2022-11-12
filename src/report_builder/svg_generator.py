import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from report_builder.abs_report_builder import AbsReportBuilder


class SvgReportBuilder(AbsReportBuilder):
    DAYS = ['Mo.', 'Di.', 'Mi.', 'Do.', 'Fr.', 'Sa.', 'So.']
    MONTHS = ['Jan.', 'Feb.', 'Mar.', 'Apr.', 'Mai', 'Juni', 'Juli', 'Aug.', 'Sept.', 'Okt.', 'Nov.', 'Dez.']

    def __plot_heatmap(self, series, start=None, end=None, mean=False, ax=None, **kwargs):
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

        dates = series.index.floor('D')
        group = series.groupby(dates)
        series = group.mean() if mean else group.sum()

        start = pd.to_datetime(start or series.index.min())
        end = pd.to_datetime(end or series.index.max())

        end += np.timedelta64(1, 'D')

        start_mon = start - np.timedelta64((start.dayofweek + 0) % 7, 'D')
        end_mon = end + np.timedelta64(7 - end.dayofweek - 0, 'D')

        num_weeks = (end_mon - start_mon).days // 7
        heatmap = np.zeros((7, num_weeks))
        ticks = {}
        for week in range(num_weeks):
            for day in range(7):
                date = start_mon + np.timedelta64(7 * week + day, 'D')
                if date.day == 1:
                    ticks[week] = MONTHS[date.month - 1]
                if date.dayofyear == 1:
                    ticks[week] += f'\n{date.year}'
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
        ax.set_yticklabels(DAYS)

        plt.sca(ax)
        plt.sci(mesh)

        return ax

    def date_heatmap(self, series):
        figsize = plt.figaspect(7 / 56)
        fig = plt.figure(figsize=figsize)

        ax = __plot_heatmap(series, edgecolor='black')
        plt.colorbar(ticks=range(5), pad=0.02)

        cmap = mpl.cm.get_cmap('Reds', 5)
        plt.set_cmap(cmap)
        plt.clim(-0.5, 4.5)

        ax.set_aspect('equal')

        fig.savefig('heatmap.svg', bbox_inches='tight', format='svg')

        plt.close(fig)
