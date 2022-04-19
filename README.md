# Extract Retrieval Data

_Formerly known as "filter-retrieval-data-v2"._

<br/>

## What is it?

This repository contains all the code for extracting measurement data from our SQL database. On https://retrieval.esm.ei.tum.de/ one can visually inspect all raw and post-processed data we have since late 2019. Using this extraction tool, one can generate CSV files containing post-processed concentration time series for specific filter settings and dates/sensors.

<br/>

## Where to run it?

You have to be inside the MWN, either physically or via a VPN (https://wiki.tum.de/display/esm/VPN).

Your system has to have **Python 3** (https://www.python.org/downloads/), **Git** (https://git-scm.com/) and a "Terminal"/"Shell"/"Command Prompt" installed. The instructions here are from a Linux environment. I highly recommend working in a Linux/macOS environment when working with code.

<br/>

## How to set it up?

Virtual environments using **venv**: https://docs.python.org/3/library/venv.html
Dependency management with **poetry**: https://python-poetry.org/docs/#installation

Set up project interpreter:

```bash
# Create a virtual environment (a local copy of python)
python3.9 -m venv .venv

# Switch to the virtual environment
source .venv/bin/activate

# Install dependencies
poetry install
```

<br/>

## How to run it?

1. Use the file `config.example.json` to create a file `config.json` for your setup

2. Run it with (using the virtual env from before):

    ```bash
    python run.py
    ```

3. Your output files will be located in `data/csv-out` and `data/json-out`. An example of a generated CSV file can be found here: https://github.com/tum-esm/extract-retrieval-data/blob/main/docs/example-out.csv

<br/>

## FAQs

### How does the filtering work?

1. Calibrate the raw measurement data, calibration factors are used from the database
2. Filter out any data where GFIT flagged some anomaly (temperature in the enclosure, rapid concentration drop, etc.)
3. Filter out any data according to specific filter cases
4. Compute a rolling mean over the remaining data
5. Resample the smooth curves at a given rate for the output files

<br/>

### What do the filter settings do?

-   `filter.movingWindowSizeMinutes` is the size of the window that is used for the rolling average to smooth the data
-   `filter.outputStepSizeMinutes` is the time between data points in the output data (`2` means there will be a row every two minutes - when there is any data after filtering).
-   An explanation of the `filter.cases` can be found in the Master Thesis of Nico Nachtigall (NAS [?](https://wiki.tum.de/display/esm/NAS): `/tuei/esm/Thesis/Masterarbeiten/2020 MA Nico Nachtigall/Nachtigall_MasterThesis_final.pdf`)

<br/>

### What other settings are there?

Have a look at `config.example.json`.

<br/>

### What does the `calibrationDays` setting do?

In an ideal setting, every location has a fixed spectrometer that is used there. Only on calibration days, some locations have other spectrometers measuring there. With `"calibrationDays": {"exportToCSV": false}` the data from a location and a different spectrometer is not considered.

A generated CSV looks something like this:

```txt
## SENSOR LOCATIONS:
##    me17: GEO
##    mb86: HAW
##    mc15: JOR
##    md16: ROS
###########################################
year_day_hour,      me17_xco2_ppm_sc, mb86_xco2_ppm_sc, mc15_xco2_ppm_sc,   md16_xco2_ppm_sc
2021-08-1206:00:59, NaN,              NaN,              412.02071425886874, NaN
```

Without that data from calibration, each column in the generated CSV - identified by spectrometer - will always have the same location. When calibration data is included, the location of one column can differ between CSV files.

**Disclaimer:** The default spectrometer for each location is given in `src/helpers/constants.py`. However, this is not fully working yet, since the default spectrometers might change over time (if spectrometers break for example). This is already being worked on: https://github.com/tum-esm/extract-retrieval-data/issues/11

<br/>

### What if I exhausted my resources and my question is still not answered?

Ask Moritz Makowski (moritz.makowski@tum.de).
