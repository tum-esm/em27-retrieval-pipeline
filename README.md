
# Retrieval Plots v2 - Python Script for Generating and Uploading Data

Full documentation coming soon! Until then, ask Moritz Makowski (moritz.makowski@tum.de).

## What is it?

The repository contains all the code for extracting measurement data from our SQL database. It combines functionality from https://gitlab.lrz.de/esm/em27-plot-data-upload and https://gitlab.lrz.de/esm/columnmeasurementautomation. However, the automation repo also includes the triggering of gfit and loading stuff into the database. These two processes (loading into database and extracting from database) should be separated in the long run. This repo implements the second process (extraction).

<br/>
<br/>

## How to set it up?

Virtual environments using **venv**: https://docs.python.org/3/library/venv.html
Dependency management with **poetry**: https://python-poetry.org/docs/#installation

Set up project interpreter:

```bash
# Create virtual environment (a local copy of python)
python3.9 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
poetry install
```

<br/>
<br/>

## How to run it?

1. Use the file `config.example.json` to create a file `config.json` for your setup

2. Modify `run.py` for your usage

3. Run it with (using the virtual env from before)
```bash
python run.py
```
