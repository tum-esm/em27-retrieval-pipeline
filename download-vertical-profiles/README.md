<h1 align="center">Download Vertical Profiles</h1>

<div align="center">

[![Continuous Integration](https://github.com/tum-esm/download-vertical-profiles/actions/workflows/continuous_integration.yml/badge.svg)](https://github.com/tum-esm/download-vertical-profiles/actions/workflows/continuous_integration.yml)

Used to download __`.map`__, __`.mod`__ and __`.vmr`__ files from __<span>ccycle.gps.caltech.edu</span>__.[^1]<br/>Samples can be found in **`docs/`**.



</div>

<hr />

## :sparkles: Getting Started
Requires __Python 3.10+__. Dependency management with __Poetry__.[^2] 


### :electric_plug: Installation
Clone the repository and set up the project interpreter
```bash
# Optional: create .venv within the project
poetry config virtualenvs.in-project true

# Install dependencies
poetry install
```

### :gear: Configuration

Create a file `config.json` to configure your setup.<br/>The configuration consists of the three sub-configurations `GitHub`, `FTP` and `Request` (see also `config.template.json`).
```python
name: Type [= Default] # Comment
```

#### :octopus: GitHub
Access to GitHub directory containing EM27 data, i.e., `campaigns.json`, `locations.json` and `sensors.json`.[^3] Note that `data_dir` must point to the raw data, i.e., in the format https://raw.githubusercontent.com/.*.
```python
username: str
token: str
data_dir: str
```
####  :floppy_disk: FTP
Settings for accessing `ccycle.gps.caltech.edu`.
```python
email: str
max_day_delay: int = 7
upload_sleep: int = 60
upload_timeout: int = 180
download_sleep: int = 60
download_timeout: int = 600
```
####  :mag_right: Request
Settings for the request. Note that the date format is **YYYYMMDD**.
```python

versions: list[Version] = ["GGG2014"]
from_date: str = "00010101"
to_date: str = utcnow()
dst_dir: str = ./vertical-profiles
```
## 🏛 Architecture
Note that the following gives a high-level overview - not the full picture.
<div align="center">
<a href="docs/architecture.png"><img src="docs/architecture.png" align="center" width="80%" ></a>
</div>

### 🚀 Operation

Run `run.py` manually

```bash
poetry run python run.py
```

**OR** configure a cron job schedule

```bash
crontab -e

# Add the following line
mm hh * * * .../.venv/bin/python .../run.py
```
## 🗄 Structure
```
./
├── .cache/
├── .github/workflows
│   └── continuous_integration.yml
├── docs/
│   └── architecture.png
├── reports/
├── src/
│   ├── custom_types/
│   │   ├── location_data_types/
│   │   │   ├── location.py
│   │   │   └── sensor.py
│   │   ├── config.py
│   │   ├── query.py
│   │   └── validators.py
│   ├── procedures/
│   │   ├── location_data.py
│   │   ├── query.py
│   │   └── sensor_set.py
│   ├── utils/
│   │   └── network.py
│   └── main.py
├── tests/
├── vertical-profiles/
├── .gitattributes
├── .gitignore
├── README.md
├── config.example.json
├── poetry.lock
├── pyproject.toml
└── run.py
```
####  :floppy_disk: `ccycle.gps.caltech.edu`
**GGG2014**
```
Directories
- upload/modfiles/tar/maps/
- upload/modfiles/tar/mods/
Archives
- maps_48N012E_20211110_20211110.tar
- mods_48N012E_20211110_20211110.tar
Files
- 2021111021_48N012E.map
- NCEP_20221209_19N_099W.mod
```
**GGG2020**
```
Directory
- ginput-jobs/
Archive
- job_000022748_tu_48.00N_12.00E_20211110-20211111.tgz
Files
- fpit/tu/maps-vertical/tu_48N_012E_2021111000Z.map 
- fpit/tu/vertical/FPIT_2021111000Z_48N_012E.mod
- fpit/tu/vmrs-vertical/JL1_2021111000Z_48N_012E.vmr
```
[^1]: TCCON: https://tccon-wiki.caltech.edu/Main/ObtainingGinputData
[^2]: Poetry Installation: https://python-poetry.org/docs/#installation
[^3]: Example Repository: https://github.com/tum-esm/em27-location-data
