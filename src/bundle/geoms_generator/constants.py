from typing import Optional


MIN_SZA: float = 0
MIN_XAIR: Optional[float] = None
MAX_XAIR: Optional[float] = None
PARSE_DC_TIMESERIES: bool = True

SITE_DESCRIPTION: str = ""

EVDC_NETWORK = "FTIR.COCCON"
EVDC_LOCATIONS = {
    "TUM_I": "MUNICH.TUM",
    "FEL": "MUNICH.FELDKIRCHEN",
    "GRAE": "MUNICH.GRAEFELFING",
    "OBE": "MUNICH.OBERSCHLEISSHEIM",
    "TAU": "MUNICH.TAUFKIRCHEN",
    "DLR_2": "MUNICH.DLR_2",
    "DLR_3": "MUNICH.DLR_3",
}
EVDC_AFFILIATION = "TUM.ESM"
EVDC_METADATA = {
    # Project
    "FILE_ACCESS": "COCCON",
    "FILE_PROJECT_ID": "COCCON",
    "DATA_DISCIPLINE": "ATMOSPHERIC.CHEMISTRY;REMOTE.SENSING;GROUNDBASED",
    "DATA_GROUP": "EXPERIMENTAL;PROFILE.STATIONARY",
    #
    # Metadata
    "DATA_FILE_VERSION": "001",
    "DATA_LOCATION": "<Registered EVDC Location>",
    "DATA_PROCESSOR": "PROFFAST Version 2.4",
    "DATA_QUALITY": "Station data.",
    "DATA_SOURCE": f"{EVDC_NETWORK}_<affiliation><3-digit serial number>",
    "DATA_TEMPLATE": "GEOMS-TE-FTIR-COCCON-001",
    "FILE_DOI": "",
    "FILE_META_VERSION": "04R088;CUSTOM",
    #
    # Pricipal Investigator
    "PI_NAME": "Chen;Jia",
    "PI_EMAIL": "jia.chen@tum.de",
    "PI_AFFILIATION": "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM",
    "PI_ADDRESS": "Theresienstr. 90;D-80333 Munich;GERMANY",
    #
    # Data Originator
    "DO_NAME": "Makowski;Moritz",
    "DO_EMAIL": "moritz.makowski@tum.de",
    "DO_AFFILIATION": "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM",
    "DO_ADDRESS": "Theresienstr. 90;D-80333 Munich;GERMANY",
    #
    # Data Submitter
    "DS_NAME": "Makowski;Moritz",
    "DS_EMAIL": "moritz.makowski@tum.de",
    "DS_AFFILIATION": "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM",
    "DS_ADDRESS": "Theresienstr. 90;D-80333 Munich;GERMANY",
}
