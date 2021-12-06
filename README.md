# Extract Retrieval Data

_Formerly known as "filter-retrieval-data-v2". Full documentation coming soon! Until then, ask Moritz Makowski (moritz.makowski@tum.de)._

<br/>

## What is it?

This repository contains all the code for extracting measurement data from our SQL database. It combines functionality from https://gitlab.lrz.de/esm/em27-plot-data-upload and https://gitlab.lrz.de/esm/columnmeasurementautomation. However, the `columnmeasurementautomation`-repo also includes the triggering of gfit and loading stuff into the database.

**These two processes (1. loading into database, 2. extracting from database) should be separated in the long run! This repository implements the second process (extraction).**

<br/>

## IMPORTANT: NOT EVERYTHING WORKS!

This repository is currently undergoing refactoring - that's why this code is not on the main branch. **The CSV export already fully works!** The JSON-export and website-upload is currently not working.

You can clone this specific branch of the repository with:

```bash
git clone -b general-extraction-tool https://github.com/tum-esm/extract-retrieval-data.git
```

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
