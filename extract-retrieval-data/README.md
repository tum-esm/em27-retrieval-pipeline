<h1 align="center">Extract Retrieval Data</h1>

<div align="center">

[![Continuous Integration](https://github.com/tum-esm/automated-retrieval-pipeline/tree/main/extract-retrieval-data/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/tum-esm/automated-retrieval-pipeline/tree/main/extract-retrieval-data/actions/workflows/continuous-integration.yml)


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

|         Name         | Type  |                             Description                             |                Default                |
| :------------------: | :---: | :-----------------------------------------------------------------: | :-----------------------------------: |
|      `campaign`      |  str  |    Email granting access to <span>ccycle.gps.caltech.edu</span>     |                   -                   |
|   `location_data`    |  str  | GitHub directory containing `locations.json` and `sensors.json`[^4] |                   -                   |
|    `git_username`    |  str  |                           GitHub username                           |                   -                   |
|     `git_token`      |  str  |                  GitHub personal access token[^5]                   |                   -                   |
| `retrieval_software` |  str  |                                                                     |                  ``                   |
|     `from_date`      |  str  |                   Start date in _YYYYMMDD_ format                   |                  ``                   |
|      `to_date`       |  str  |                    End date in _YYYYMMDD_ format                    |                  ``                   |
|   `dst_directory`    |  str  |                          Output directory                           | `PROJECT_PATH/retrieval-FIXME - data` |


### 🚀 Operation

Run `extract_retrieval_data.py`

```bash
poetry run python extract_retrieval_data.py
```

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
│   ├──
│   └── architecture.png
├── src/
│   ├── types/
│   │   ├── configuration.py
│   │   └──
├── retrieval-data/
├── .gitattributes
├── .gitignore
├── README.md
├── extract_retrieval_data.py
├── poetry.lock
└── pyproject.toml
```
[^1]: 
[^2]: Predecessor: 
[^3]: Poetry Installation: https://python-poetry.org/docs/#installation
[^4]: Example Repository: https://github.com/tum-esm/em27-location-data
[^5]: GitHub Tokens: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token