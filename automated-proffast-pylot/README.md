# Automated Proffast Pylot

This is a wrapper around https://gitlab.eudat.eu/coccon-kit/proffastpylot for our setup.

_work in progress, until then, ask Moritz Makowski and Patrick Aigner_

<br/>

## File Movements

![](/docs/architecture.png)

_This chart only the flow from automatic upload to retrieval outputs. The manual queue mentioned in the scheduling section can take other inputs as well._

<br/>

## Installation

**Only works in Unix systems!**

1. Install Python3.9: https://python.org/

2. Install Poetry: https://python-poetry.org/

3. Install Gfortran: https://fortran-lang.org/learn/os_setup/install_gfortran

4. Download and compile all proffast for this project

```bash
bash scripts/installation/install-prf-submodules.sh
```

5. Install python dependencies

```bash
python3.10 -m venv .venv
source .venv/bin/activate
poetry install
```

<br/>

6. Use `config/config.example.json` to generate a file `config/config.json` for your setup

7. Download the location data for your stations

```bash
python scripts/installation/fetch-location-data.py
```

<br/>

## Procedure Steps

What the `automated-proffast-pylot` does:

1. **What days are there to be processed next?** Considers all days in `/mnt/measurementData/mu`, processes the latest dates first.

2. **Copy all inputs to `/home/esm/automation-pipelines/automated-proffast-pylot`.** First look for datalogger- and map-file. If these do not exist, abort this day. If they exist, copy them and the interferograms into the working directory of the proffast-pylot.

3. **Run the proffast pylot.** The Pylot only works on the local directories `inputs/` and `outputs/`.

4. **Copy the results onto the DSS for long-term storage.** If Proffast did not encounter any errors, there will be a file `combined_invparms_SS_YYYYMMDD-YYYYMMDD.csv` in the day's output folder. Depending on success or not, copy the output folder of proffast into `/home/esm/em27_ifg_dss/proffast_archive/SS/proffast-outputs/` or `.../proffast-outputs-failed/`. Copy the original interferograms (from `/mnt/measurementData/mu`) into `/home/esm/em27_ifg_dss/proffast_archive/SS/ifgs/`.

<br/>

## Scheduling

**What day will the automation process next?**

**1.** Look into the file `manual-queue.json`. Take the job with the _highest priority greater than 0_ - inside the same priority class, with the latest date.

_... if there are no high-priority jobs:_

**2.** Look into the directory specified by `config["src"]["interferograms"]["upload"]` and take the latest date from there.

_... if there are no jobs in the upload directory:_

**3.** Take the remaining files from `manual-queue.json` (priority < 0). Order by descending priority and the descending date - same as in step 1.

_... end iteration if no more days to process_

<br/>

Steps 1 and 3 will only be considered, when the file `manual-queue.json` exists and is in a valid format. Only priorities ≠ 0 are valid. If the file was found but is invalid, the logs will contain warnings about that. Example file:

```json
[
    { "sensor": "ma", "date": "20220101", "priority": 10 },
    { "sensor": "mb", "date": "20220101", "priority": 9 },
    { "sensor": "mc", "date": "20220101", "priority": -10 }
]
```

The manual queue (step 1 and 3) will look for files on `config["dst"]`, `config["src"]["interferograms"]["upload"]` as well as all locations specified in `config["src"]["interferograms"]["other"]`. If there are multiple directories containing ifgs files for a day and station, it will check, whether these directories are identical. If not, this sensor-day will be aborted and there will be an error in the logs. If they are identical, the automation can take any of them as input.

This manual queue can be used for **rerunning the retrieval** for certain (failed) days, etc. or to **prioritize certain days** in the upload directory over others.

We will include scripts to automatically add failed proffast-retrieval days to the queue soon.

<br/>

## Logging & Cron

The automation will log everything in `logs/YYYYMMDD-HH-MM.log`. `YYYYMMDD` is the date, `HH-MM` is the time. The timestamp is determined by the starting date and time of the execution.

Add the script to your crontab with the following line. This will try to start the automation every 3 hours - in case it is not already running.

```bash
0 0,3,6,9,12,15,18,21 * * * .../.venv/bin/python .../run.py
```

<br/>

## Comments on Architectural Decisions

The Pylot would allow us to **process multiple days for one sensor in parallel**. However, there are multiple drawbacks to this:

-   If one day fails, the Pylot will not finish any of the days
-   There is one merged output file and output folder, which makes naming conventions rather very confusing (without a lot of conversions)
-   The queue-building is unnecessarily complicated because the Pylot can only handle days with the same sensor at the same location

<br/>

The Pylot could do more of the file moving than we are using it for. However, this data is very valuable and I don't want PROFFAST or the Pylot to work on the original files. The copying scripts here are very short and have built-in security steps so that no data will be deleted. Since PROFFAST and the Pylot do way more than this codebase, verifying them is quite hard.

<br/>

## Temporary Notes

Rerun retrieval for the following dates - these have been retrieved using incorrect coordinates:

```
mb
20210108  20210116  20210810  20220127  20210110  20210320  20210115  20210808

me
20210415  20210808  20210815  20210827  20210926  20210809  20210821  20210906
```

## Start/Stop pipeline as a background process

```
python cli/main.py start
python cli/main.py is-running
python cli/main.py stop
```
