# Download Vertical Profiles

_Formerly: https://github.com/tum-esm/download-map-data_

## 🔍 What is it?

This tool can be used to download `.map` and `.mod` files from `ccycle.gps.caltech.edu`. These files contain vertical distributions of meteorological parameters for a certain location and date. The underlying accessing method is described on https://tccon-wiki.caltech.edu/Main/CentralizedModMaker. A sample `.map` and `.mod` can be found in `docs/`.

It uses the template repository https://github.com/tum-esm/em27-location-data-template for location management. Running the script `fetch-location-data.py` will clone the respective repository and run its integrity checks.

<br/>
<br/>

## 🔌 How to run it?

Dependency management with poetry: https://python-poetry.org/docs/#installation

1. Set up the project interpreter:

```bash
# Create a virtual python environment
python3.9 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
poetry install
```

2. Use the file `config.default.json` to create a `config.json` file in your project directory for your setup

3. Download location data

```bash
python fetch-location-data.py
```

4. Run the script and wait for the result

```bash
python main.py
```

5. OR: Run the script in a cron-job to always keep this dataset up-to-date

```bash
crontab -e

# add the following line to the list
mm hh * * * .../.venv/bin/python .../main.py
```

<br/>

**Responses from Caltech will be cached** in the `cache/` directory. If you want your duplicate requests to be faster and use fewer computing resources, do not remove or empty this directory.

<br/>
<br/>

## ⚙️ Configuration

**from/to:** Self-explaining.

**user:** Your user email that is used to log onto `ccycle.gps.caltech.edu`. See: https://tccon-wiki.caltech.edu/Main/CentralizedModMaker

**dst:** The directory where output files will be placed.

**downloadTimeoutSeconds:** The `ccycle.gps.caltech.edu` will take a while to generate the profiles. This defines, how long this tool will wait until it aborts trying to download the profiles.

**locationRepository:** A repository structured like https://github.com/tum-esm/em27-location-data-template

<br/>
<br/>

## 🏛 Architecture

![](/docs/architecture.png)

_For more details, please look into the code itself._
