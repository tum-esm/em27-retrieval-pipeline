<h1 align="center">Download Vertical Profiles</h1>

<div align="center">

[![Continuous Integration](https://github.com/tum-esm/download-vertical-profiles/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/tum-esm/download-vertical-profiles/actions/workflows/continuous-integration.yml)

Used to download __`.map`__, __`.mod`__ and __`.vmr`__ files from __<span>ccycle.gps.caltech.edu</span>__.[^1] [^2] <br /> Sample files can be found in `docs/example-profiles`.

</div>

<hr />

## Getting Started
Requires __Python 3.10+__. Dependency management with __Poetry__.[^3] 

### :electric_plug: Installation
Clone the repository and set up the project interpreter
```bash
# Optional: create .venv within the project
poetry config virtualenvs.in-project true

# Install dependencies
poetry install
```

### :gear: Configuration

Create a file `config/config.json` to configure your setup.<br/>An example `config.example.json` can be found in `config/`.

|      Name      | Type  |                             Description                             |             Default              |
| :------------: | :---: | :-----------------------------------------------------------------: | :------------------------------: |
|    `email`     |  str  |    Email granting access to <span>ccycle.gps.caltech.edu</span>     |                -                 |
| `locationData` |  str  | GitHub directory containing `locations.json` and `sensors.json`[^4] |                -                 |
| `gitUsername`  |  str  |                           GitHub username                           |                -                 |
|   `gitToken`   |  str  |                  GitHub personal access token[^5]                   |                -                 |
|  `fromDate`   |  str  |                   Start date in _YYYYMMDD_ format                   |            `00010101`            |
|   `toDate`    |  str  |                    End date in _YYYYMMDD_ format                    |       `datetime.utcnow()`        |
| `dstDirectory` |  str  |                          Output directory                           | `PROJECT_PATH/vertical-profiles` |
| `maxAwait2014` |  int  |                          Wall time awaiting GGG2014 data until abortion in seconds                           | `600` |
| `maxAwait2020` |  int  |                          Wall time awaiting GGG2020 data until abortion in seconds                           | `10_000` |
| `maxDelay` |  int  |                          Maximum days of data lag                           | `7` |

### 🚀 Operation

Run `download_vertical_profiles.py` manually

```bash
poetry run python download_vertical_profiles.py
```

**OR** configure a cron job schedule

```bash
crontab -e

# Add the following line
mm hh * * * .../.venv/bin/python .../download_vertical_profiles.py
```

`GGG2020` data takes a long time to generate, thus make sure to set a proper `from_date`.

Execution summaries are stored within `reports/`.

## 🏛 Architecture
<a href="docs/architecture.png"><img src="docs/architecture.png" align="center" width="100%" ></a>
## 🗄 Structure
```
./
├── .github/workflows
│   └── continuous-integration.yml
├── config/
│   └── config.example.json
├── docs/
│   ├── example-profiles/
│   │   ├── GGG2014/
│   │   └── GGG2020/
│   └── architecture.png
├── reports/
├── src/
│   ├── types/
│   │   ├── configuration.py
│   │   └── location.py
│   ├── utils/
│   │   └── network.py
│   └── query_list.py
├── tests/
│   └── test_query_list.py
├── vertical-profiles/
├── .gitattributes
├── .gitignore
├── README.md
├── download_vertical_profiles.py
├── poetry.lock
└── pyproject.toml
```
[^1]: TCCON: https://tccon-wiki.caltech.edu/Main/DataUsePolicy, https://tccon-wiki.caltech.edu/Main/ObtainingGinputData
[^2]: Predecessor: https://github.com/tum-esm/download-map-data.
[^3]: Poetry Installation: https://python-poetry.org/docs/#installation
[^4]: Example Repository: https://github.com/tum-esm/em27-location-data
[^5]: GitHub Tokens: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
