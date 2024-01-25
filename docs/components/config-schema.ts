/* prettier-ignore */
const CONFIG_SCHEMA: any = {
    "description": "A pydantic model describing the config file schema.",
    "properties": {
        "version": {
            "const": "1.0",
            "description": "Version of the retrieval pipeline which is compatible with this config file. Retrievals done with any version `1.x` will produce the same output files as retrievals done with version `1.0`. But higher version numbers might use a different config file structure and produce more output files.",
            "title": "Version"
        },
        "general": {
            "properties": {
                "metadata": {
                    "anyOf": [
                        {
                            "description": "GitHub repository where the location data is stored.",
                            "properties": {
                                "github_repository": {
                                    "description": "GitHub repository name, e.g. `my-org/my-repo`.",
                                    "pattern": "^[a-z0-9-_]+/[a-z0-9-_]+$",
                                    "title": "Github Repository",
                                    "type": "string"
                                },
                                "access_token": {
                                    "anyOf": [
                                        {
                                            "minLength": 1,
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "GitHub access token with read access to the repository, only required if the repository is private.",
                                    "title": "Access Token"
                                }
                            },
                            "required": [
                                "github_repository"
                            ],
                            "title": "MetadataConfig",
                            "type": "object"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "If not set, the pipeline will use local metadata files or abort if the local files are not found. If local files are found, they will always be preferred over the remote data even if the remote source is configured."
                },
                "data": {
                    "description": "Location where the input data sourced from.",
                    "properties": {
                        "datalogger": {
                            "description": "directory path to datalogger files",
                            "title": "StrictDirectoryPath",
                            "type": "string"
                        },
                        "atmospheric_profiles": {
                            "description": "directory path to atmospheric profile files",
                            "title": "StrictDirectoryPath",
                            "type": "string"
                        },
                        "interferograms": {
                            "description": "directory path to ifg files",
                            "title": "StrictDirectoryPath",
                            "type": "string"
                        },
                        "results": {
                            "description": "directory path to results",
                            "title": "StrictDirectoryPath",
                            "type": "string"
                        }
                    },
                    "required": [
                        "datalogger",
                        "atmospheric_profiles",
                        "interferograms",
                        "results"
                    ],
                    "title": "DataConfig",
                    "type": "object"
                }
            },
            "required": [
                "data"
            ],
            "title": "GeneralConfig",
            "type": "object"
        },
        "profiles": {
            "anyOf": [
                {
                    "description": "Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning",
                    "properties": {
                        "server": {
                            "description": "Settings for accessing the ccycle ftp server. Besides the\n`email` field, these can be left as default in most cases.",
                            "properties": {
                                "email": {
                                    "description": "Email address to use to log in to the ccycle ftp server.",
                                    "minLength": 3,
                                    "title": "Email",
                                    "type": "string"
                                },
                                "max_parallel_requests": {
                                    "description": "Maximum number of requests to put in the queue on the ccycle server at the same time. Only when a request is finished, a new one can enter the queue.",
                                    "maximum": 200,
                                    "minimum": 1,
                                    "title": "Max Parallel Requests",
                                    "type": "integer"
                                }
                            },
                            "required": [
                                "email",
                                "max_parallel_requests"
                            ],
                            "title": "ProfilesServerConfig",
                            "type": "object"
                        },
                        "scope": {
                            "properties": {
                                "from_date": {
                                    "default": "1900-01-01",
                                    "description": "date in format `YYYY-MM-DD` from which to request vertical profile data.",
                                    "format": "date",
                                    "title": "From Date",
                                    "type": "string"
                                },
                                "to_date": {
                                    "default": "2100-01-01",
                                    "description": "date in format `YYYY-MM-DD` until which to request vertical profile data.",
                                    "format": "date",
                                    "title": "To Date",
                                    "type": "string"
                                },
                                "models": {
                                    "description": "list of data types to request from the ccycle ftp server.",
                                    "items": {
                                        "enum": [
                                            "GGG2014",
                                            "GGG2020"
                                        ],
                                        "type": "string"
                                    },
                                    "title": "Models",
                                    "type": "array"
                                }
                            },
                            "required": [
                                "models"
                            ],
                            "title": "ProfilesScopeConfig",
                            "type": "object"
                        },
                        "GGG2020_standard_sites": {
                            "description": "List of standard sites to request from the ccycle ftp server. The requests for these standard sites are done before any other requests so that data available for these is not rerequested for other sensors.",
                            "items": {
                                "properties": {
                                    "identifier": {
                                        "description": "The identifier on the caltech server",
                                        "title": "Identifier",
                                        "type": "string"
                                    },
                                    "lat": {
                                        "maximum": 90.0,
                                        "minimum": -90.0,
                                        "title": "Lat",
                                        "type": "number"
                                    },
                                    "lon": {
                                        "maximum": 180.0,
                                        "minimum": -180.0,
                                        "title": "Lon",
                                        "type": "number"
                                    },
                                    "from_date": {
                                        "description": "Date in format `YYYY-MM-DD` from which this standard site is active.",
                                        "format": "date",
                                        "title": "From Date",
                                        "type": "string"
                                    },
                                    "to_date": {
                                        "description": "Date in format `YYYY-MM-DD` until which this standard site is active.",
                                        "format": "date",
                                        "title": "To Date",
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "identifier",
                                    "lat",
                                    "lon",
                                    "from_date",
                                    "to_date"
                                ],
                                "title": "ProfilesGGG2020StandardSitesItemConfig",
                                "type": "object"
                            },
                            "title": "Ggg2020 Standard Sites",
                            "type": "array"
                        }
                    },
                    "required": [
                        "server",
                        "scope",
                        "GGG2020_standard_sites"
                    ],
                    "title": "ProfilesConfig",
                    "type": "object"
                },
                {
                    "type": "null"
                }
            ],
            "default": null
        },
        "retrieval": {
            "anyOf": [
                {
                    "description": "Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning",
                    "properties": {
                        "general": {
                            "properties": {
                                "max_process_count": {
                                    "default": 1,
                                    "description": "How many parallel processes to dispatch. There will be one process per sensor-day. With hyper-threaded CPUs, this can be higher than the number of physical cores.",
                                    "maximum": 128,
                                    "minimum": 1,
                                    "title": "Max Process Count",
                                    "type": "integer"
                                },
                                "ifg_file_regex": {
                                    "description": "A regex string to match the ifg file names. In this string, `$(SENSOR_ID)` and `$(DATE)` are placeholders for the sensor id and the date of the ifg file.",
                                    "examples": [
                                        "^$(SENSOR_ID)$(DATE).*\\.\\d+$",
                                        "^$(SENSOR_ID)$(DATE).*\\.nc$"
                                    ],
                                    "minLength": 1,
                                    "title": "Ifg File Regex",
                                    "type": "string"
                                }
                            },
                            "required": [
                                "ifg_file_regex"
                            ],
                            "title": "RetrievalGeneralConfig",
                            "type": "object"
                        },
                        "jobs": {
                            "description": "List of retrievals to run. The list will be processed sequentially.",
                            "items": {
                                "description": "Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`.",
                                "properties": {
                                    "retrieval_algorithm": {
                                        "description": "Which retrieval algorithms to use. Proffast 2.2 and 2.3 use the Proffast Pylot under the hood to dispatch it. Proffast 1.0 uses a custom implementation by us similar to the Proffast Pylot.",
                                        "enum": [
                                            "proffast-1.0",
                                            "proffast-2.2",
                                            "proffast-2.3"
                                        ],
                                        "title": "Retrieval Algorithm",
                                        "type": "string"
                                    },
                                    "atmospheric_profile_model": {
                                        "description": "Which vertical profiles to use for the retrieval.",
                                        "enum": [
                                            "GGG2014",
                                            "GGG2020"
                                        ],
                                        "title": "Atmospheric Profile Model",
                                        "type": "string"
                                    },
                                    "sensor_ids": {
                                        "description": "Sensor ids to consider in the retrieval.",
                                        "items": {
                                            "type": "string"
                                        },
                                        "minItems": 1,
                                        "title": "Sensor Ids",
                                        "type": "array"
                                    },
                                    "from_date": {
                                        "description": "Date string in format `YYYY-MM-DD` from which to consider data in the storage directory.",
                                        "format": "date",
                                        "title": "From Date",
                                        "type": "string"
                                    },
                                    "to_date": {
                                        "description": "Date string in format `YYYY-MM-DD` until which to consider data in the storage directory.",
                                        "format": "date",
                                        "title": "To Date",
                                        "type": "string"
                                    },
                                    "settings": {
                                        "properties": {
                                            "store_binary_spectra": {
                                                "default": false,
                                                "description": "Whether to store the binary spectra files. These are the files that are used by the retrieval algorithm. They are not needed for the output files, but can be useful for debugging.",
                                                "title": "Store Binary Spectra",
                                                "type": "boolean"
                                            },
                                            "dc_min_threshold": {
                                                "default": 0.05,
                                                "description": "Value used for the `DC_min` threshold in Proffast. If not set, defaults to the Proffast default.",
                                                "maximum": 0.999,
                                                "minimum": 0.001,
                                                "title": "Dc Min Threshold",
                                                "type": "number"
                                            },
                                            "dc_var_threshold": {
                                                "default": 0.1,
                                                "description": "Value used for the `DC_var` threshold in Proffast. If not set, defaults to the Proffast default.",
                                                "maximum": 0.999,
                                                "minimum": 0.001,
                                                "title": "Dc Var Threshold",
                                                "type": "number"
                                            }
                                        },
                                        "title": "RetrievalJobSettingsConfig",
                                        "type": "object",
                                        "default": {
                                            "store_binary_spectra": false,
                                            "dc_min_threshold": 0.05,
                                            "dc_var_threshold": 0.1
                                        },
                                        "description": "Advanced settings that only apply to this retrieval job"
                                    }
                                },
                                "required": [
                                    "retrieval_algorithm",
                                    "atmospheric_profile_model",
                                    "sensor_ids",
                                    "from_date",
                                    "to_date"
                                ],
                                "title": "RetrievalJobConfig",
                                "type": "object"
                            },
                            "title": "Jobs",
                            "type": "array"
                        }
                    },
                    "required": [
                        "general",
                        "jobs"
                    ],
                    "title": "RetrievalConfig",
                    "type": "object"
                },
                {
                    "type": "null"
                }
            ],
            "default": null
        },
        "export_targets": {
            "anyOf": [
                {
                    "items": {
                        "properties": {
                            "campaign_id": {
                                "description": "Campaign specified in location metadata.",
                                "title": "Campaign Id",
                                "type": "string"
                            },
                            "retrieval_algorithm": {
                                "description": "Which retrieval algorithm used for the retrieval.",
                                "enum": [
                                    "proffast-1.0",
                                    "proffast-2.2",
                                    "proffast-2.3"
                                ],
                                "title": "Retrieval Algorithm",
                                "type": "string"
                            },
                            "atmospheric_profile_model": {
                                "description": "Which atmospheric profiles used for the retrieval.",
                                "enum": [
                                    "GGG2014",
                                    "GGG2020"
                                ],
                                "title": "Atmospheric Profile Model",
                                "type": "string"
                            },
                            "data_types": {
                                "description": "Data columns to keep in the merged output files. The columns will be prefixed with the sensor id, i.e. `$(SENSOR_ID)_$(COLUMN_NAME)`.",
                                "items": {
                                    "enum": [
                                        "gnd_p",
                                        "gnd_t",
                                        "app_sza",
                                        "azimuth",
                                        "xh2o",
                                        "xair",
                                        "xco2",
                                        "xch4",
                                        "xco",
                                        "xch4_s5p"
                                    ],
                                    "type": "string"
                                },
                                "minItems": 1,
                                "title": "Data Types",
                                "type": "array"
                            },
                            "sampling_rate": {
                                "description": "Interval of resampled data.",
                                "enum": [
                                    "10m",
                                    "5m",
                                    "2m",
                                    "1m",
                                    "30s",
                                    "15s",
                                    "10s",
                                    "5s",
                                    "2s",
                                    "1s"
                                ],
                                "title": "Sampling Rate",
                                "type": "string"
                            },
                            "max_interpolation_gap_seconds": {
                                "default": 180,
                                "description": "Maximum gap in seconds to interpolate over.",
                                "maximum": 43200,
                                "minimum": 6,
                                "title": "Max Interpolation Gap Seconds",
                                "type": "integer"
                            },
                            "dst_dir": {
                                "description": "Directory to write the output to.",
                                "title": "StrictDirectoryPath",
                                "type": "string"
                            }
                        },
                        "required": [
                            "campaign_id",
                            "retrieval_algorithm",
                            "atmospheric_profile_model",
                            "data_types",
                            "sampling_rate",
                            "dst_dir"
                        ],
                        "title": "ExportTargetConfig",
                        "type": "object"
                    },
                    "type": "array"
                },
                {
                    "type": "null"
                }
            ],
            "default": null,
            "description": "List of output merging targets. Relies on specifying \"campaigns\" in the EM27 metadata.",
            "title": "Export Targets"
        }
    },
    "required": [
        "version",
        "general"
    ],
    "title": "Config",
    "type": "object"
};

export default CONFIG_SCHEMA;