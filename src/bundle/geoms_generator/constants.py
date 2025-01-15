from typing import Optional


MIN_SZA: float = 0
MIN_XAIR: Optional[float] = None
MAX_XAIR: Optional[float] = None
PARSE_DC_TIMESERIES: bool = True

SITE_DESCRIPTION: str = "TODO"


HDF_METADATA = {
    # Project
    "FILE_ACCESS": "COCCON",
    "FILE_PROJECT_ID": "COCCON",
    "DATA_DISCIPLINE": "ATMOSPHERIC.CHEMISTRY;REMOTE.SENSING;GROUNDBASED",
    "DATA_GROUP": "EXPERIMENTAL;PROFILE.STATIONARY",
    #
    # Metadata
    "DATA_FILE_VERSION": "001",
    "DATA_LOCATION": "MUNICH",
    "DATA_PROCESSOR": "PROFFAST Version 2.4",
    "DATA_QUALITY": "Station data.",
    "DATA_SOURCE": "FTIR.COCCON_TUM_ma061_TUM_I",
    "DATA_TEMPLATE": "GEOMS-TE-FTIR-COCCON-001",
    "FILE_DOI": "",
    "FILE_META_VERSION": "04R088;CUSTOM",
    #
    # Pricipal Investigator
    "PI_NAME": "TODO",
    "PI_EMAIL": "TODO",
    "PI_AFFILIATION": "TODO",
    "PI_ADDRESS": "TODO",
    #
    # Data Originator
    "DO_NAME": "TODO",
    "DO_EMAIL": "TODO",
    "DO_AFFILIATION": "TODO",
    "DO_ADDRESS": "TODO",
    #
    # Data Submitter
    "DS_NAME": "TODO",
    "DS_EMAIL": "TODO",
    "DS_AFFILIATION": "TODO",
    "DS_ADDRESS": "TODO",
}
