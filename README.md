# Extract Retrieval Data

_Formerly known as "filter-retrieval-data-v2"._

<br/>

## What is it?

This repository contains all the code for extracting measurement data from our SQL database. It combines functionality from https://gitlab.lrz.de/esm/em27-plot-data-upload and https://gitlab.lrz.de/esm/columnmeasurementautomation. However, the `columnmeasurementautomation`-repo also includes the triggering of gfit and loading stuff into the database.

**These two processes (1. loading into the database, 2. extracting from the database) should be separated! This repository implements the second process (extraction).**

<br/>

## Where to run it?

You have to be inside the TUM network, either physically or via a VPN.

As of right now, you have to set up this tool on your machine. In the future, we will have a group VM running Linux, where you can run tools like this and have all dependencies already installed. Details about this will come in January.

Your system has to have **Python 3** (https://www.python.org/downloads/), **Git** (https://git-scm.com/) and a "Terminal"/"Shell"/"Command Prompt". The instructions here are from a Linux environment. I highly recommend you to work in a Linux environment when working with code.

<br/>

## How to set it up?

Virtual environments using **venv**: https://docs.python.org/3/library/venv.html
Dependency management with **poetry**: https://python-poetry.org/docs/#installation

Set up project interpreter:

```bash
# Create virtual environment (a local copy of python)
python3.9 -m venv .venv

# Switch to virtual environment
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

<br/>

## FAQs

**How does the filtering work?**

1. Calibrate the raw measurement data, calibration factors are used from the database
2. Filter out any data where gfit flagged some anomaly (temperature in the enclosure, rapid concentration drop, etc.)
3. Filter out any data according to specific filter cases
4. Compute a rolling mean over the remaining data
5. Resample the smooth curves at a given rate for the output files

**What do the filter settings do?**

-   `filter.movingWindowSizeMinutes` is the size of the window that is used for the rolling average to smooth the data
-   `filter.outputStepSizeMinutes` is the time between data points in the output data (`2` means there will be a row every two minutes - when there is any data after filtering).
-   An explanation on the `filter.cases` can be found in the Master Thesis of Nico Nachtigall (NAS: `/tuei/esm/Thesis/Masterarbeiten/2020 MA Nico Nachtigall/Nachtigall_MasterThesis_final.pdf`)

**How do I access the NAS?**

See https://wiki.tum.de/display/esm/NAS

**What other settings are there?**

Have a look at `config.example.json`.

**What does the `calibrationDays` setting do?**

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

**What if I exhausted my resources and my question is still not answered?**

Ask Moritz Makowski (moritz.makowski@tum.de).
