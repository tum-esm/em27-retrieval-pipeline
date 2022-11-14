import numpy as np
import pandas
from datetime import datetime


def date_to_timestamp(date: str):
    date = str(int(date))
    if len(date) == 8:
        return int(
            datetime(int(date[:4]), int(date[4:6]), int(date[6:]), 0, 0, 0).timestamp()
        )
    if len(date) == 6:
        return int(datetime(int(date[:4]), int(date[4:6]), 15, 0, 0, 0).timestamp())
    if len(date) == 4:
        return int(datetime(int(date[:4]), 6, 15, 0, 0, 0).timestamp())
    else:
        raise "invalid date format"


# reading the CSV file
csvFile = pandas.read_csv("data.csv")

# define data
x = np.array(list(map(date_to_timestamp, list(csvFile["t"]))))
data = {
    "co2": np.array(csvFile["AVG(xco2_ppm)"]),
    "ch4": np.array(csvFile["AVG(xch4_ppm)"]),
    "co": np.array(csvFile["AVG(xco_ppb)"]),
}

# find line of best fit
best_fits = {gas: np.polyfit(x, data[gas], 1) for gas in data}

# best fit: y = a*x + b
for gas in best_fits:
    print(
        f"{gas}: y = {round(best_fits[gas][0] * 3600*24*365.25, 3)} * t + {round(best_fits[gas][1], 3)}"
    )

""" 
SELECT * FROM (
    SELECT ((Date - (Date % 10000))/10000) as d, AVG(xco2_ppm), AVG(xch4_ppm), AVG(xco_ppb), Count(*) as c, STDDEV(xco2_ppm)
    FROM `measuredValues`
    WHERE ID_Location IN ('TUM_I') AND Flag = 0 AND Date > 20190913
    GROUP BY d
) a WHERE c > 500
"""
