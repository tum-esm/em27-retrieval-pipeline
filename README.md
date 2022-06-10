# Automated Proffast Pylot

This a wrapper around https://gitlab.eudat.eu/coccon-kit/proffastpylot for our setup.

_work in progress, until then, ask Moritz Makowski and Patrick Aigner_

<br/>

## File Movements

![](/docs/architecture.png)

<br/>

## Procedure Steps

What the `automated-proffast-pylot` does:

1. **What days are there to be processed next?** Considers all days in `/mnt/measurementData/mu`, processes the latest dates first.

2. **Copy all inputs to `/home/esm/automation-pipelines/automated-proffast-pylot`.** First look for datalogger- and map-file. If these do not exist, abort this day. If they exist, copy them and the interferograms into the working directory of the proffast-pylot.

3. **Run the proffast pylot.** The Pylot only works on the local directories `inputs/` and `outputs/`.

4. **Copy the results onto the DSS for long-term storage.** If Proffast did not encounter any errors, there will be a file `combined_invparms_SS_YYYYMMDD-YYYYMMDD.csv` in the day's output folder. Depending on success or not, copy the output folder of proffast into `/home/esm/em27_ifg_dss/proffast_archive/SS/proffast-outputs/` or `.../proffast-outputs-failed/`. Copy the original interferograms (from `/mnt/measurementData/mu`) into `/home/esm/em27_ifg_dss/proffast_archive/SS/ifgs/`.

<br/>

## Logging & Cron

The automation will log everything in `logs/YYYYMMDD-HH-MM.log`. `YYYYMMDD` is the date, `HH-MM` is the time. The timestamp is determined by the starting date and time of the execution.

Additionally, the retrieval-queue used in that execution will be written to `logs/automation/YYYYMMDD-HH-MM-queue.json`.

Add the script to your crontab with the following line. This will try to start the automation every 3 hours - in case it is not already running.

```bash
0 0,3,6,9,12,15,18,21 * * * .../.venv/bin/python .../main.py
```

<br/>

## Comments on Architectural Decisions

The pylot would allow us to **process multiple days for one sensor in parallel**. However, there are multiple drawbacks to this:

-   If one day fails, the pylot will not finish any of the days
-   There is one merged output file and output folder, which makes naming conventions rather very confusing (without a lot of conversion)
-   The queue-building is unnessecarily complicated because the pylot can only handle days with the same sensor at the same location

<br/>

The Pylot could actually do more of the file moving than we are using it for. However, this data is very valuable and I don't want PROFFAST or the Pylot to work on the original files. The copying scripts in here are very short and have built-in security-steps so that no data will be deleted. Since PROFFAST and the Pylot do way more than this codebase, verifying them is quite hard.

<br/>

## Temporary Notes

Rerun retrieval for the following dates - these have been retrieved using incorrect coordinates:

```
mb
20210108  20210116  20210810  20220127  20210110  20210320  20210115  20210808

me
20210415  20210808  20210815  20210827  20210926  20210809  20210821  20210906
```
