<h1 align="center">Extract Retrieval Data</h1>

<div align="center">

[![Continuous Integration](https://github.com/tum-esm/automated-retrieval-pipeline/tree/main/extract-retrieval-data/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/tum-esm/automated-retrieval-pipeline/tree/main/extract-retrieval-data/actions/workflows/continuous_integration.yml)

Generates CSV files containing post-processed concentration time series.<br/>A sample can be found in **`docs/`.**

</div>

<hr />

## :sparkles: Getting Started

Requires **Python 3.10+**. Dependency management with **Poetry**.[^1]

### :electric_plug: Installation

Clone the repository and set up the project interpreter

```bash
# Optional: create .venv within the project
poetry config virtualenvs.in-project true

# Install dependencies
poetry install
```

### :gear: Configuration

Create a file `config.json` to configure your setup.<br/>The configuration consists of the three sub-configurations `GitHub`, `Database` and `Request` (see also `config.template.json`).

```python
name: Type [= Default] # Comment
```

#### :octopus: GitHub

Access to GitHub directory containing EM27 data, i.e., `campaigns.json`, `locations.json` and `sensors.json`.[^2] Note that `data_dir` must point to the raw data, i.e., in the format https://raw.githubusercontent.com/.\*.

```python
username: str
token: str
data_dir: str
```

#### :floppy_disk: Database

Access to PostgreSQL database containing retrieval data.

```python
host: str
username: str
password: str
database_name: str
port: str = "5432"
table_name: str = "measurements"
```

#### :mag_right: Request

Settings for the retrieval process. Note that the date format is **YYYYMMDD**.

```python
campaign_name: str
from_date: str = "00010101"
to_date: str = utcnow()
proffast_version: str = "2.2"
data_types: DataType = [
    "gnd_p",
    "gnd_t",
    "app_sza",
    "azimuth",
    "xh2o",
    "xair",
    "xco2",
    "xch4",
    "xco",
    "xch4_s5p",
]
sampling_rate: Rate = "1 min"
dst_dir: str = ./retrieval-data
```

### 🚀 Operation

Run `run.py`

```bash
poetry run python run.py
```

For the requested period, the tool generates one `<campaign_name>_em27_export_<date>.csv` file per day.

## :hammer_and_wrench: Post-processing

_TBD_

## 🏛 Architecture

Note that the following gives a high-level overview - not the full picture.

<div align="center">
<a href="docs/architecture.png"><img src="docs/architecture.png" align="center" width="80%" ></a>
</div>

## 🗄 Structure

```
./
├── .github/workflows
│   └── continuous_integration.yml
├── docs/
│   ├── muccnet_em27_export_20210101.csv
│   └── architecture.png
├── retrieval-data/
├── src/
│   ├── custom_types/
│   │   ├── location_data_types/
│   │   │   ├── campaign.py
│   │   │   ├── location.py
│   │   │   └── sensor.py
│   │   ├── config.py
│   │   └── validators.py
│   ├── procedures/
│   │   ├── dataframe.py
│   │   ├── location_data.py
│   │   ├── metadata.py
│   │   └── sensor_set.py
│   ├── utils/
│   │   └── network.py
│   └── main.py
├── tests/
├── .gitattributes
├── .gitignore
├── README.md
├── config.example.json
├── poetry.lock
├── pyproject.toml
└── run.py
```

[^1]: Poetry Installation: https://python-poetry.org/docs/#installation
[^2]: Example Repository: https://github.com/tum-esm/em27-location-data
