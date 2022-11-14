from datetime import datetime

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from report_builder.abs_report_builder import AbsReportBuilder


class CsvReportBuilder(AbsReportBuilder):
    def create_output(self, subreport_name: str, series: pd.Series):
        pass

    def save_file(self):
        pass

    data = {
        "date": [],
        "sensor": [],
        "count": []
    }

    def save_heatmap(self):
        dates = np.asarray([datetime(2021, 5, 17), datetime(2021, 5, 17), datetime(2021, 5, 17), 7, 9]).reshape(6, 5)
        perchange = np.asarray([1, 3, 5, 7, 9]).reshape(6, 5)

        # result = df.pivot(index='Yrows', columns='Xcols', values='Change')

        labels = (np.asarray(["{0} \n {1:.2f}".format(symb, value)
                              for symb, value in zip(symbol.flatten(),
                                                     perchange.flatten())])
                  ).reshape(6, 5)

        # Define the plot
        fig, ax = plt.subplots(figsize=(13, 7))

        # Add title to the Heat map
        title = "Pharma Sector Heat Map"

        # Set the font size and the distance of the title from the plot
        plt.title(title, fontsize=18)
        ttl = ax.title
        ttl.set_position([0.5, 1.05])

        # Hide ticks for X & Y axis
        ax.set_xticks([])
        ax.set_yticks([])

        # Remove the axes
        ax.axis('off')

        # Use the heatmap function from the seaborn package
        sns.heatmap(result, annot=labels, fmt="", cmap='RdYlGn', linewidths=0.30, ax=ax)

        # Display the Pharma Sector Heatmap
        plt.show()
