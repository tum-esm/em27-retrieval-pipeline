/* prettier-ignore */
const CONFIG_SCHEMA: any = {
    "additionalProperties": false,
    "description": "A pydantic model describing the config file schema.",
    "properties": {
        "version": {
            "const": "1.5",
            "description": "Version of the retrieval pipeline which is compatible with this config file. Retrievals done with any version `1.x` will produce the same output files as retrievals done with version `1.0`. But higher version numbers might use a different config file structure and produce more output files.",
            "title": "Version",
            "type": "string"
        },
        "general": {
            "additionalProperties": false,
            "properties": {
                "metadata": {
                    "anyOf": [
                        {
                            "additionalProperties": false,
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
                    "additionalProperties": false,
                    "description": "Location where the input data sourced from.",
                    "properties": {
                        "ground_pressure": {
                            "additionalProperties": false,
                            "description": "directory path and format configuration of the ground pressure files",
                            "properties": {
                                "path": {
                                    "title": "StrictDirectoryPath",
                                    "type": "string",
                                    "description": "Directory path to ground pressure files."
                                },
                                "file_regex": {
                                    "description": "A regex string to match the ground pressure file names. In this string, you can use the placeholders `$(SENSOR_ID)`, `$(YYYY)`, `$(YY)`, `$(MM)`, and `$(DD)` to make this regex target a certain station and date. The placeholder `$(DATE)` is a shortcut for `$(YYYY)$(MM)$(DD)`.",
                                    "examples": [
                                        "^$(DATE).tsv$",
                                        "^$(SENSOR_ID)_$(DATE).dat$",
                                        "^ground-pressure-$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).csv$"
                                    ],
                                    "minLength": 1,
                                    "title": "File Regex",
                                    "type": "string"
                                },
                                "separator": {
                                    "description": "Separator used in the ground pressure files. Only needed and used if the file format is `text`.",
                                    "examples": [
                                        ",",
                                        "\t",
                                        " ",
                                        ";"
                                    ],
                                    "maxLength": 1,
                                    "minLength": 1,
                                    "title": "Separator",
                                    "type": "string"
                                },
                                "datetime_column": {
                                    "anyOf": [
                                        {
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Column name in the ground pressure files that contains the datetime.",
                                    "examples": [
                                        "datetime",
                                        "dt",
                                        "utc-datetime"
                                    ],
                                    "title": "Datetime Column"
                                },
                                "datetime_column_format": {
                                    "anyOf": [
                                        {
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Format of the datetime column in the ground pressure files.",
                                    "examples": [
                                        "%Y-%m-%dT%H:%M:%S"
                                    ],
                                    "title": "Datetime Column Format"
                                },
                                "date_column": {
                                    "anyOf": [
                                        {
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Column name in the ground pressure files that contains the date.",
                                    "examples": [
                                        "date",
                                        "d",
                                        "utc-date"
                                    ],
                                    "title": "Date Column"
                                },
                                "date_column_format": {
                                    "anyOf": [
                                        {
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Format of the date column in the ground pressure files.",
                                    "examples": [
                                        "%Y-%m-%d",
                                        "%Y%m%d",
                                        "%d.%m.%Y"
                                    ],
                                    "title": "Date Column Format"
                                },
                                "time_column": {
                                    "anyOf": [
                                        {
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Column name in the ground pressure files that contains the time.",
                                    "examples": [
                                        "time",
                                        "t",
                                        "utc-time"
                                    ],
                                    "title": "Time Column"
                                },
                                "time_column_format": {
                                    "anyOf": [
                                        {
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Format of the time column in the ground pressure files.",
                                    "examples": [
                                        "%H:%M:%S",
                                        "%H:%M",
                                        "%H%M%S"
                                    ],
                                    "title": "Time Column Format"
                                },
                                "unix_timestamp_column": {
                                    "anyOf": [
                                        {
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Column name in the ground pressure files that contains the unix timestamp.",
                                    "examples": [
                                        "unix-timestamp",
                                        "timestamp",
                                        "ts"
                                    ],
                                    "title": "Unix Timestamp Column"
                                },
                                "unix_timestamp_column_format": {
                                    "anyOf": [
                                        {
                                            "enum": [
                                                "s",
                                                "ms",
                                                "us",
                                                "ns"
                                            ],
                                            "type": "string"
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "default": null,
                                    "description": "Format of the unix timestamp column in the ground pressure files. I.e. is the Unix timestamp in seconds, milliseconds, etc.?",
                                    "title": "Unix Timestamp Column Format"
                                },
                                "pressure_column": {
                                    "description": "Column name in the ground pressure files that contains the pressure.",
                                    "examples": [
                                        "pressure",
                                        "p",
                                        "ground_pressure"
                                    ],
                                    "title": "Pressure Column",
                                    "type": "string"
                                },
                                "pressure_column_format": {
                                    "description": "Unit of the pressure column in the ground pressure files.",
                                    "enum": [
                                        "hPa",
                                        "Pa",
                                        "bar",
                                        "mbar",
                                        "atm",
                                        "psi",
                                        "inHg",
                                        "mmHg"
                                    ],
                                    "title": "Pressure Column Format",
                                    "type": "string"
                                }
                            },
                            "required": [
                                "path",
                                "file_regex",
                                "separator",
                                "pressure_column",
                                "pressure_column_format"
                            ],
                            "title": "GroundPressureConfig",
                            "type": "object"
                        },
                        "atmospheric_profiles": {
                            "title": "StrictDirectoryPath",
                            "type": "string",
                            "description": "directory path to atmospheric profile files"
                        },
                        "interferograms": {
                            "title": "StrictDirectoryPath",
                            "type": "string",
                            "description": "directory path to ifg files"
                        },
                        "results": {
                            "title": "StrictDirectoryPath",
                            "type": "string",
                            "description": "directory path to results"
                        }
                    },
                    "required": [
                        "ground_pressure",
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
                    "additionalProperties": false,
                    "description": "Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning",
                    "properties": {
                        "server": {
                            "additionalProperties": false,
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
                            "anyOf": [
                                {
                                    "additionalProperties": false,
                                    "properties": {
                                        "from_date": {
                                            "default": "1900-01-01",
                                            "description": "Date in format `YYYY-MM-DD` from which to request vertical profile data.",
                                            "format": "date",
                                            "title": "From Date",
                                            "type": "string"
                                        },
                                        "to_date": {
                                            "default": "2100-01-01",
                                            "description": "Date in format `YYYY-MM-DD` until which to request vertical profile data.",
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
                                {
                                    "type": "null"
                                }
                            ],
                            "default": null,
                            "description": "Scope of the vertical profiles to request from the ccycle ftp server. If set to `null`, the script will not request any vertical profiles besides the configured standard sites."
                        },
                        "GGG2020_standard_sites": {
                            "description": "List of standard sites to request from the ccycle ftp server. The requests for these standard sites are done before any other requests so that data available for these is not rerequested for other sensors. See https://tccon-wiki.caltech.edu/Main/ObtainingGinputData#Requesting_to_be_added_as_a_standard_site for more information.",
                            "items": {
                                "additionalProperties": false,
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
                    "additionalProperties": false,
                    "description": "Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning",
                    "properties": {
                        "general": {
                            "additionalProperties": false,
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
                                    "description": "A regex string to match the ifg file names. In this string, `$(SENSOR_ID)`, `$(YYYY)`, `$(YY)`, `$(MM)`, and `$(DD)` are placeholders to target a certain station and date. The placeholder `$(DATE)` is a shortcut for `$(YYYY)$(MM)$(DD)`. They don't have to be used - you can also run the retrieval on any file it finds in the directory using `.*`",
                                    "examples": [
                                        "^*\\.\\d+$^$(SENSOR_ID)$(DATE).*\\.\\d+$",
                                        "^$(SENSOR_ID)-$(YYYY)-$(MM)-$(DD).*\\.nc$"
                                    ],
                                    "minLength": 1,
                                    "title": "Ifg File Regex",
                                    "type": "string"
                                },
                                "queue_verbosity": {
                                    "default": "compact",
                                    "description": "How much information the retrieval queue should print out. In `verbose` mode it will print out the full list of sensor-days for each step of the filtering process. This can help when figuring out why a certain sensor-day is not processed.",
                                    "enum": [
                                        "compact",
                                        "verbose"
                                    ],
                                    "title": "Queue Verbosity",
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
                                "additionalProperties": false,
                                "description": "Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`.",
                                "properties": {
                                    "retrieval_algorithm": {
                                        "description": "Which retrieval algorithms to use. Proffast 2.X uses the Proffast Pylot under the hood to dispatch it. Proffast 1.0 uses a custom implementation by us similar to the Proffast Pylot.",
                                        "enum": [
                                            "proffast-1.0",
                                            "proffast-2.2",
                                            "proffast-2.3",
                                            "proffast-2.4",
                                            "proffast-2.4.1"
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
                                        "additionalProperties": false,
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
                                            },
                                            "use_local_pressure_in_pcxs": {
                                                "default": false,
                                                "description": "Whether to use the local pressure in the pcxs files. If not used, it will tell PCXS to use the pressure from the atmospheric profiles (set the input value in the `.inp` file to `9999.9`). If used, the pipeline computes the solar noon time using `skyfield` and averages the local pressure over the time period noon-2h to noon+2h.",
                                                "title": "Use Local Pressure In Pcxs",
                                                "type": "boolean"
                                            },
                                            "use_ifg_corruption_filter": {
                                                "default": true,
                                                "description": "Whether to use the ifg corruption filter. This filter is a program based on `preprocess4` and is part of the `tum-esm-utils` library: https://tum-esm-utils.netlify.app/api-reference#tum_esm_utilsinterferograms. If activated, we will only pass the interferograms to the retrieval algorithm that pass the filter - i.e. that won't cause it to crash.",
                                                "title": "Use Ifg Corruption Filter",
                                                "type": "boolean"
                                            },
                                            "custom_ils": {
                                                "additionalProperties": {
                                                    "additionalProperties": false,
                                                    "properties": {
                                                        "channel1_me": {
                                                            "title": "Channel1 Me",
                                                            "type": "number"
                                                        },
                                                        "channel1_pe": {
                                                            "title": "Channel1 Pe",
                                                            "type": "number"
                                                        },
                                                        "channel2_me": {
                                                            "title": "Channel2 Me",
                                                            "type": "number"
                                                        },
                                                        "channel2_pe": {
                                                            "title": "Channel2 Pe",
                                                            "type": "number"
                                                        }
                                                    },
                                                    "required": [
                                                        "channel1_me",
                                                        "channel1_pe",
                                                        "channel2_me",
                                                        "channel2_pe"
                                                    ],
                                                    "title": "RetrievalJobSettingsILSConfig",
                                                    "type": "object"
                                                },
                                                "default": {},
                                                "description": "Maps sensor IDS to ILS correction values. If not set, the pipeline will use the values published inside the Proffast Pylot codebase (https://gitlab.eudat.eu/coccon-kit/proffastpylot/-/blob/master/prfpylot/ILSList.csv?ref_type=heads).",
                                                "title": "Custom Ils",
                                                "type": "object"
                                            },
                                            "output_suffix": {
                                                "anyOf": [
                                                    {
                                                        "type": "string"
                                                    },
                                                    {
                                                        "type": "null"
                                                    }
                                                ],
                                                "default": null,
                                                "description": "Suffix to append to the output folders. If not set, the pipeline output folders are named `sensorid/YYYYMMDD/`. If set, the folders are named `sensorid/YYYYMMDD_suffix/`. This is useful when having multiple retrieval jobs processing the same sensor dates with different settings.",
                                                "title": "Output Suffix"
                                            },
                                            "pressure_calibration_factors": {
                                                "additionalProperties": {
                                                    "type": "number"
                                                },
                                                "default": {},
                                                "description": "Maps sensor IDS to pressure calibration factors. If not set, it is set to 1 for each sensor. `corrected_pressure = input_pressure * calibration_factor + calibration_offset`",
                                                "examples": [
                                                    "{\"ma\": 0.99981}",
                                                    "{\"ma\": 1.00019, \"mb\": 0.99981}"
                                                ],
                                                "title": "Pressure Calibration Factors",
                                                "type": "object"
                                            },
                                            "pressure_calibration_offsets": {
                                                "additionalProperties": {
                                                    "type": "number"
                                                },
                                                "default": {},
                                                "description": "Maps sensor IDS to pressure calibration offsets. If not set, it is set to 0 for each sensor. `corrected_pressure = input_pressure * calibration_factor + calibration_offset`",
                                                "examples": [
                                                    "{\"ma\": -0.00007}",
                                                    "{\"ma\": -0.00007, \"mb\": 0.00019}"
                                                ],
                                                "title": "Pressure Calibration Offsets",
                                                "type": "object"
                                            }
                                        },
                                        "title": "RetrievalJobSettingsConfig",
                                        "type": "object",
                                        "default": {
                                            "store_binary_spectra": false,
                                            "dc_min_threshold": 0.05,
                                            "dc_var_threshold": 0.1,
                                            "use_local_pressure_in_pcxs": false,
                                            "use_ifg_corruption_filter": true,
                                            "custom_ils": {},
                                            "output_suffix": null,
                                            "pressure_calibration_factors": {},
                                            "pressure_calibration_offsets": {}
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
        "bundles": {
            "anyOf": [
                {
                    "items": {
                        "additionalProperties": false,
                        "description": "There will be one file per sensor id and atmospheric profile and retrieval algorithm combination.\n\nThe final name looks like `em27-retrieval-bundle-$SENSOR_ID-$RETRIEVAL_ALGORITHM-$ATMOSPHERIC_PROFILE-$FROM_DATE-$TO_DATE$BUNDLE_SUFFIX.$OUTPUT_FORMAT`, e.g.`em27-retrieval-bundle-ma-GGG2020-proffast-2.4-20150801-20240523-v2.1.csv`. The bundle suffix is optional and can be used to distinguish between different\ninternal datasets.",
                        "properties": {
                            "dst_dir": {
                                "title": "StrictDirectoryPath",
                                "type": "string",
                                "description": "Directory to write the bundeled outputs to."
                            },
                            "output_formats": {
                                "description": "List of output formats to write the merged output files in.",
                                "items": {
                                    "enum": [
                                        "csv",
                                        "parquet"
                                    ],
                                    "type": "string"
                                },
                                "title": "Output Formats",
                                "type": "array"
                            },
                            "from_datetime": {
                                "description": "Date in format `YYYY-MM-DDTHH:MM:SS` from which to bundle data",
                                "format": "date-time",
                                "title": "From Datetime",
                                "type": "string"
                            },
                            "to_datetime": {
                                "description": "Date in format `YYYY-MM-DDTHH:MM:SS` to which to bundle data",
                                "format": "date-time",
                                "title": "To Datetime",
                                "type": "string"
                            },
                            "retrieval_algorithms": {
                                "description": "The retrieval algorithms for which to bundle the outputs",
                                "items": {
                                    "enum": [
                                        "proffast-1.0",
                                        "proffast-2.2",
                                        "proffast-2.3",
                                        "proffast-2.4",
                                        "proffast-2.4.1"
                                    ],
                                    "type": "string"
                                },
                                "title": "Retrieval Algorithms",
                                "type": "array"
                            },
                            "atmospheric_profile_models": {
                                "description": "The atmospheric profile models for which to bundle the outputs",
                                "items": {
                                    "enum": [
                                        "GGG2014",
                                        "GGG2020"
                                    ],
                                    "type": "string"
                                },
                                "title": "Atmospheric Profile Models",
                                "type": "array"
                            },
                            "sensor_ids": {
                                "description": "The sensor ids for which to bundle the outputs",
                                "items": {
                                    "type": "string"
                                },
                                "title": "Sensor Ids",
                                "type": "array"
                            },
                            "bundle_suffix": {
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
                                "description": "Suffix to append to the output bundles.",
                                "examples": [
                                    "v2.1",
                                    "v2.2",
                                    "oco2-gradient-paper-2021"
                                ],
                                "title": "Bundle Suffix"
                            },
                            "retrieval_job_output_suffix": {
                                "anyOf": [
                                    {
                                        "type": "string"
                                    },
                                    {
                                        "type": "null"
                                    }
                                ],
                                "default": null,
                                "description": "When you ran the retrieval with a custom suffix, you can specify it here to only bundle the outputs of this suffix. Use the same value here as in the field `config.retrieval.jobs[i].settings.output_suffix`.",
                                "title": "Retrieval Job Output Suffix"
                            },
                            "parse_dc_timeseries": {
                                "default": false,
                                "description": "Whether to parse the DC timeseries from the results directories. This is an output only available in this Pipeline for Proffast2.4. We adapted the preprocessor to output the DC min/mean/max/variation values for each record of data. If you having issues with a low signal intensity on one or both channels, you can run the retrieval with a very low DC_min threshold and filter the data afterwards instead of having to rerun the retrieval.",
                                "title": "Parse Dc Timeseries",
                                "type": "boolean"
                            }
                        },
                        "required": [
                            "dst_dir",
                            "output_formats",
                            "from_datetime",
                            "to_datetime",
                            "retrieval_algorithms",
                            "atmospheric_profile_models",
                            "sensor_ids"
                        ],
                        "title": "BundleTargetConfig",
                        "type": "object"
                    },
                    "type": "array"
                },
                {
                    "type": "null"
                }
            ],
            "default": null,
            "description": "List of output bundling targets.",
            "title": "Bundles"
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