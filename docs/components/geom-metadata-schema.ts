/* prettier-ignore */
const GEOM_METADATA_SCHEMA: any = {
    "properties": {
        "general": {
            "properties": {
                "network": {
                    "description": "Used in the filename of the HDF5 file",
                    "examples": [
                        "FTIR.COCCON"
                    ],
                    "title": "Network",
                    "type": "string"
                },
                "affiliation": {
                    "description": "Used in the filename of the HDF5 file",
                    "examples": [
                        "TUM.ESM"
                    ],
                    "title": "Affiliation",
                    "type": "string"
                },
                "pressure_sensor_name": {
                    "description": "The value of the HDF5 attribute `SURFACE.PRESSURE_INDEPENDENT_SOURCE`",
                    "examples": [
                        "young-61302",
                        "vaisala-PTB330"
                    ],
                    "title": "Pressure Sensor Name",
                    "type": "string"
                }
            },
            "required": [
                "network",
                "affiliation",
                "pressure_sensor_name"
            ],
            "title": "GEOMSGeneralMetadata",
            "type": "object"
        },
        "data": {
            "properties": {
                "discipline": {
                    "description": "The value of the HDF5 attribute `DATA_DISCIPLINE`",
                    "examples": [
                        "ATMOSPHERIC.CHEMISTRY;REMOTE.SENSING;GROUNDBASED"
                    ],
                    "title": "Discipline",
                    "type": "string"
                },
                "group": {
                    "description": "The value of the HDF5 attribute `DATA_GROUP`",
                    "examples": [
                        "EXPERIMENTAL;PROFILE.STATIONARY"
                    ],
                    "title": "Group",
                    "type": "string"
                },
                "file_version": {
                    "description": "The value of the HDF5 attribute `DATA_FILE_VERSION`",
                    "examples": [
                        1
                    ],
                    "title": "File Version",
                    "type": "integer"
                },
                "quality": {
                    "description": "The value of the HDF5 attribute `DATA_QUALITY`",
                    "examples": [
                        "Station data."
                    ],
                    "title": "Quality",
                    "type": "string"
                },
                "template": {
                    "description": "The value of the HDF5 attribute `DATA_TEMPLATE`",
                    "examples": [
                        "GEOMS-TE-FTIR-COCCON-001"
                    ],
                    "title": "Template",
                    "type": "string"
                }
            },
            "required": [
                "discipline",
                "group",
                "file_version",
                "quality",
                "template"
            ],
            "title": "GEOMSDataMetadata",
            "type": "object"
        },
        "file": {
            "properties": {
                "doi": {
                    "description": "The value of the HDF5 attribute `FILE_DOI`",
                    "title": "Doi",
                    "type": "string"
                },
                "meta_version": {
                    "description": "The value of the HDF5 attribute `FILE_META_VERSION`",
                    "examples": [
                        "04R088;CUSTOM"
                    ],
                    "title": "Meta Version",
                    "type": "string"
                },
                "access": {
                    "description": "The value of the HDF5 attribute `FILE_ACCESS`",
                    "examples": [
                        "COCCON"
                    ],
                    "title": "Access",
                    "type": "string"
                },
                "project_id": {
                    "description": "The value of the HDF5 attribute `FILE_PROJECT_ID`",
                    "examples": [
                        "COCCON"
                    ],
                    "title": "Project Id",
                    "type": "string"
                }
            },
            "required": [
                "doi",
                "meta_version",
                "access",
                "project_id"
            ],
            "title": "GEOMSFileMetadata",
            "type": "object"
        },
        "principle_investigator": {
            "properties": {
                "name": {
                    "description": "The value of the HDF5 attribute `PI_NAME`/`DO_NAME`/`DS_NAME`",
                    "examples": [
                        "Makowski;Moritz"
                    ],
                    "title": "Name",
                    "type": "string"
                },
                "email": {
                    "description": "The value of the HDF5 attribute `PI_EMAIL`/`DO_EMAIL`/`DS_EMAIL`",
                    "examples": [
                        "moritz.makowski@tum.de"
                    ],
                    "title": "Email",
                    "type": "string"
                },
                "affiliation": {
                    "description": "The value of the HDF5 attribute `PI_AFFILIATION`/`DO_AFFILIATION`/`DS_AFFILIATION`",
                    "examples": [
                        "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM"
                    ],
                    "title": "Affiliation",
                    "type": "string"
                },
                "address": {
                    "description": "The value of the HDF5 attribute `PI_ADDRESS`/`DO_ADDRESS`/`DS_ADDRESS`",
                    "examples": [
                        "Theresienstr. 90;D-80333 Munich;GERMANY"
                    ],
                    "title": "Address",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "email",
                "affiliation",
                "address"
            ],
            "title": "GEOMSContactlMetadata",
            "type": "object"
        },
        "data_originator": {
            "properties": {
                "name": {
                    "description": "The value of the HDF5 attribute `PI_NAME`/`DO_NAME`/`DS_NAME`",
                    "examples": [
                        "Makowski;Moritz"
                    ],
                    "title": "Name",
                    "type": "string"
                },
                "email": {
                    "description": "The value of the HDF5 attribute `PI_EMAIL`/`DO_EMAIL`/`DS_EMAIL`",
                    "examples": [
                        "moritz.makowski@tum.de"
                    ],
                    "title": "Email",
                    "type": "string"
                },
                "affiliation": {
                    "description": "The value of the HDF5 attribute `PI_AFFILIATION`/`DO_AFFILIATION`/`DS_AFFILIATION`",
                    "examples": [
                        "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM"
                    ],
                    "title": "Affiliation",
                    "type": "string"
                },
                "address": {
                    "description": "The value of the HDF5 attribute `PI_ADDRESS`/`DO_ADDRESS`/`DS_ADDRESS`",
                    "examples": [
                        "Theresienstr. 90;D-80333 Munich;GERMANY"
                    ],
                    "title": "Address",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "email",
                "affiliation",
                "address"
            ],
            "title": "GEOMSContactlMetadata",
            "type": "object"
        },
        "data_submitter": {
            "properties": {
                "name": {
                    "description": "The value of the HDF5 attribute `PI_NAME`/`DO_NAME`/`DS_NAME`",
                    "examples": [
                        "Makowski;Moritz"
                    ],
                    "title": "Name",
                    "type": "string"
                },
                "email": {
                    "description": "The value of the HDF5 attribute `PI_EMAIL`/`DO_EMAIL`/`DS_EMAIL`",
                    "examples": [
                        "moritz.makowski@tum.de"
                    ],
                    "title": "Email",
                    "type": "string"
                },
                "affiliation": {
                    "description": "The value of the HDF5 attribute `PI_AFFILIATION`/`DO_AFFILIATION`/`DS_AFFILIATION`",
                    "examples": [
                        "Technical University of Munich - Professorship of Environmental Sensing and Modeling;TUM.ESM"
                    ],
                    "title": "Affiliation",
                    "type": "string"
                },
                "address": {
                    "description": "The value of the HDF5 attribute `PI_ADDRESS`/`DO_ADDRESS`/`DS_ADDRESS`",
                    "examples": [
                        "Theresienstr. 90;D-80333 Munich;GERMANY"
                    ],
                    "title": "Address",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "email",
                "affiliation",
                "address"
            ],
            "title": "GEOMSContactlMetadata",
            "type": "object"
        },
        "locations": {
            "additionalProperties": {
                "type": "string"
            },
            "description": "Maps your locations id to the corresponding EVDC location id",
            "title": "Locations",
            "type": "object"
        }
    },
    "required": [
        "general",
        "data",
        "file",
        "principle_investigator",
        "data_originator",
        "data_submitter",
        "locations"
    ],
    "title": "GEOMSMetadata",
    "type": "object"
};

export default GEOM_METADATA_SCHEMA;