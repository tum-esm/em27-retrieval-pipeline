import ZodConfigType from './config-schema-type';

/* prettier-ignore */
const CONFIG_SCHEMA_OBJECT: ZodConfigType = {
  "title": "Config",
  "type": "object",
  "properties": {
    "general": {
      "title": "GeneralConfig",
      "type": "object",
      "properties": {
        "location_data": {
          "title": "LocationDataConfig",
          "description": "GitHub repository where the location data is stored",
          "type": "object",
          "properties": {
            "github_repository": {
              "title": "Github Repository",
              "description": "GitHub repository name, e.g. `my-org/my-repo`",
              "pattern": "^[a-z0-9-_]+/[a-z0-9-_]+$",
              "type": "string"
            },
            "access_token": {
              "title": "Access Token",
              "description": "GitHub access token with read access to the repository, only required if the repository is private",
              "minLength": 1,
              "type": "string"
            }
          },
          "required": [
            "github_repository"
          ]
        },
        "data_src_dirs": {
          "title": "DataSrcDirsConfig",
          "description": "Location where the input data sourced from",
          "type": "object",
          "properties": {
            "datalogger": {
              "title": "Datalogger",
              "description": "directory path to datalogger files",
              "type": "string"
            },
            "vertical_profiles": {
              "title": "Vertical Profiles",
              "description": "directory path to vertical profile files",
              "type": "string"
            },
            "interferograms": {
              "title": "Interferograms",
              "description": "directory path to ifg files",
              "type": "string"
            }
          },
          "required": [
            "datalogger",
            "vertical_profiles",
            "interferograms"
          ]
        },
        "data_dst_dirs": {
          "title": "DataDstDirsConfig",
          "type": "object",
          "properties": {
            "results": {
              "title": "Results",
              "description": "directory path to results",
              "type": "string"
            }
          },
          "required": [
            "results"
          ]
        }
      },
      "required": [
        "location_data",
        "data_src_dirs",
        "data_dst_dirs"
      ]
    },
    "vertical_profiles": {
      "title": "VerticalProfilesConfig",
      "description": "Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning",
      "type": "object",
      "properties": {
        "ftp_server": {
          "title": "VerticalProfilesFTPServerConfig",
          "description": "Settings for accessing the ccycle ftp server. Besides the\n`email` field, these can be left as default in most cases.",
          "type": "object",
          "properties": {
            "email": {
              "title": "Email",
              "description": "email address to use to log in to the ccycle ftp server",
              "minLength": 3,
              "type": "string"
            },
            "max_day_delay": {
              "title": "Max Day Delay",
              "description": "maximum number of days of data availability delay of the ccycle ftp server. For example, on day 20 with `max delay = 7` the server should have data up to at least day 13. This is necessary because when requesting data from day 1-20 the output file might be names `day_1_13.tar` or `day_1_14.tar` -> with a delay of 7 days, the download process does not look for possible files named `day_1_12.tar`, `day_1_11.tar.`, etc.",
              "default": 7,
              "minimum": 0,
              "maximum": 10,
              "type": "integer"
            },
            "upload_sleep": {
              "title": "Upload Sleep",
              "description": "TODO",
              "default": 60,
              "minimum": 0,
              "type": "integer"
            },
            "upload_timeout": {
              "title": "Upload Timeout",
              "description": "TODO",
              "default": 180,
              "minimum": 0,
              "type": "integer"
            },
            "download_sleep": {
              "title": "Download Sleep",
              "description": "TODO",
              "default": 60,
              "minimum": 0,
              "type": "integer"
            },
            "download_timeout": {
              "title": "Download Timeout",
              "description": "in seconds, how long to wait for a `.tar` file to be generated before aborting the download",
              "default": 600,
              "minimum": 0,
              "type": "integer"
            }
          },
          "required": [
            "email"
          ]
        },
        "request_scope": {
          "title": "VerticalProfilesRequestScopeConfig",
          "type": "object",
          "properties": {
            "from_date": {
              "title": "From Date",
              "description": "date string in format `YYYYMMDD` from which to request vertical profile data",
              "default": "19000101",
              "type": "string"
            },
            "to_date": {
              "title": "To Date",
              "description": "date string in format `YYYYMMDD` until which to request vertical profile data",
              "default": "21000101",
              "type": "string"
            },
            "data_types": {
              "title": "Data Types",
              "description": "list of data types to request from the ccycle ftp server",
              "default": [
                "GGG2014",
                "GGG2020"
              ],
              "minItems": 1,
              "type": "array",
              "items": {
                "enum": [
                  "GGG2014",
                  "GGG2020"
                ],
                "type": "string"
              }
            }
          }
        }
      },
      "required": [
        "ftp_server",
        "request_scope"
      ]
    },
    "automated_proffast": {
      "title": "AutomatedProffastConfig",
      "description": "Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning",
      "type": "object",
      "properties": {
        "general": {
          "title": "AutomatedProffastGeneralConfig",
          "type": "object",
          "properties": {
            "max_core_count": {
              "title": "Max Core Count",
              "description": "How many cores to use for parallel processing. There will be one process per sensor-day.",
              "default": 1,
              "minimum": 1,
              "maximum": 64,
              "type": "integer"
            },
            "ifg_file_regex": {
              "title": "Ifg File Regex",
              "description": "A regex string to match the ifg file names. In this string, `$(SENSOR_ID)` and `$(DATE)` are placeholders for the sensor id and the date of the ifg file.",
              "default": "^$(SENSOR_ID)$(DATE).*\\.\\d+$",
              "minLength": 1,
              "type": "string"
            }
          }
        },
        "data_sources": {
          "title": "AutomatedProffastDataSourcesConfig",
          "description": "Which data sources to use (storage/manual queue)",
          "type": "object",
          "properties": {
            "storage": {
              "title": "Storage",
              "description": "Whether to use the storage data. Run every sensor-day, where there is input data (`config.data_src_dirs.interferograms`) but no output data (`config.data_dst_dirs.results`).",
              "default": true,
              "type": "boolean"
            },
            "manual_queue": {
              "title": "Manual Queue",
              "description": "Whether to use the manual queue. Compute a sensor-day if data is available at `config.data_src_dirs.interferograms`, independently of results-existence. Will overwrite existing results.",
              "default": true,
              "type": "boolean"
            }
          }
        },
        "modified_ifg_file_permissions": {
          "title": "AutomatedProffastModifiedIfgFilePermissionsConfig",
          "type": "object",
          "properties": {
            "during_processing": {
              "title": "During Processing",
              "description": "A unix-like file permission string, e.g. `rwxr-xr-x`. This can be used to make the ifg files read-only during processing, to avoid accidental modification. Only used if not `null`.",
              "pattern": "^((r|-)(w|-)(x|-)){3}$",
              "type": "string"
            },
            "after_processing": {
              "title": "After Processing",
              "description": "A unix-like file permission string, e.g. `rwxr-xr-x`. Same as `during_processing`, but restoring the permissions after processing. Only used if not `null`.",
              "pattern": "^((r|-)(w|-)(x|-)){3}$",
              "type": "string"
            }
          }
        },
        "storage_data_filter": {
          "title": "AutomatedProffastStorageDataFilterConfig",
          "description": "Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`.",
          "type": "object",
          "properties": {
            "sensor_ids_to_consider": {
              "title": "Sensor Ids To Consider",
              "description": "Sensor ids to consider in the retrieval",
              "minItems": 1,
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "from_date": {
              "title": "From Date",
              "description": "Date string in format `YYYYMMDD` from which to consider data in the storage directory",
              "default": "19000101",
              "type": "string"
            },
            "to_date": {
              "title": "To Date",
              "description": "Date string in format `YYYYMMDD` until which to consider data in the storage directory",
              "default": "21000101",
              "type": "string"
            },
            "min_days_delay": {
              "title": "Min Days Delay",
              "description": "Minimum numbers of days to wait until processing. E.g. the vertical profiles from ccyle are available with a delay of 5 days, so it doesn't make sence to try processing earlier and get a lot of error messages because of missing vertical profiles.",
              "default": 5,
              "minimum": 0,
              "maximum": 60,
              "type": "integer"
            }
          },
          "required": [
            "sensor_ids_to_consider"
          ]
        }
      },
      "required": [
        "general",
        "data_sources",
        "modified_ifg_file_permissions",
        "storage_data_filter"
      ]
    },
    "output_merging_targets": {
      "title": "Output Merging Targets",
      "description": "List of output merging targets. Relies on specifying \"campaigns\" in the EM27 metadata.",
      "default": [],
      "type": "array",
      "items": {
        "title": "OutputMergingTargetConfig",
        "type": "object",
        "properties": {
          "campaign_id": {
            "title": "Campaign Id",
            "description": "Campaign specified in location metadata.",
            "type": "string"
          },
          "sampling_rate": {
            "title": "Sampling Rate",
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
            "type": "string"
          },
          "dst_dir": {
            "title": "Dst Dir",
            "description": "Directory to write the output to.",
            "type": "string"
          },
          "data_types": {
            "title": "Data Types",
            "description": "Data columns to keep in the merged output files. The columns will be prefixed with the sensor id, i.e. `$(SENSOR_ID)_$(COLUMN_NAME)`.",
            "default": [
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
            "minItems": 1,
            "type": "array",
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
            }
          },
          "max_interpolation_gap_seconds": {
            "title": "Max Interpolation Gap Seconds",
            "description": "Maximum gap in seconds to interpolate over.",
            "default": 180,
            "minimum": 6,
            "maximum": 43200,
            "type": "integer"
          }
        },
        "required": [
          "campaign_id",
          "sampling_rate",
          "dst_dir"
        ]
      }
    }
  },
  "required": [
    "general"
  ],
  "definitions": {
    "LocationDataConfig": {
      "title": "LocationDataConfig",
      "description": "GitHub repository where the location data is stored",
      "type": "object",
      "properties": {
        "github_repository": {
          "title": "Github Repository",
          "description": "GitHub repository name, e.g. `my-org/my-repo`",
          "pattern": "^[a-z0-9-_]+/[a-z0-9-_]+$",
          "type": "string"
        },
        "access_token": {
          "title": "Access Token",
          "description": "GitHub access token with read access to the repository, only required if the repository is private",
          "minLength": 1,
          "type": "string"
        }
      },
      "required": [
        "github_repository"
      ]
    },
    "DataSrcDirsConfig": {
      "title": "DataSrcDirsConfig",
      "description": "Location where the input data sourced from",
      "type": "object",
      "properties": {
        "datalogger": {
          "title": "Datalogger",
          "description": "directory path to datalogger files",
          "type": "string"
        },
        "vertical_profiles": {
          "title": "Vertical Profiles",
          "description": "directory path to vertical profile files",
          "type": "string"
        },
        "interferograms": {
          "title": "Interferograms",
          "description": "directory path to ifg files",
          "type": "string"
        }
      },
      "required": [
        "datalogger",
        "vertical_profiles",
        "interferograms"
      ]
    },
    "DataDstDirsConfig": {
      "title": "DataDstDirsConfig",
      "type": "object",
      "properties": {
        "results": {
          "title": "Results",
          "description": "directory path to results",
          "type": "string"
        }
      },
      "required": [
        "results"
      ]
    },
    "GeneralConfig": {
      "title": "GeneralConfig",
      "type": "object",
      "properties": {
        "location_data": {
          "title": "LocationDataConfig",
          "description": "GitHub repository where the location data is stored",
          "type": "object",
          "properties": {
            "github_repository": {
              "title": "Github Repository",
              "description": "GitHub repository name, e.g. `my-org/my-repo`",
              "pattern": "^[a-z0-9-_]+/[a-z0-9-_]+$",
              "type": "string"
            },
            "access_token": {
              "title": "Access Token",
              "description": "GitHub access token with read access to the repository, only required if the repository is private",
              "minLength": 1,
              "type": "string"
            }
          },
          "required": [
            "github_repository"
          ]
        },
        "data_src_dirs": {
          "title": "DataSrcDirsConfig",
          "description": "Location where the input data sourced from",
          "type": "object",
          "properties": {
            "datalogger": {
              "title": "Datalogger",
              "description": "directory path to datalogger files",
              "type": "string"
            },
            "vertical_profiles": {
              "title": "Vertical Profiles",
              "description": "directory path to vertical profile files",
              "type": "string"
            },
            "interferograms": {
              "title": "Interferograms",
              "description": "directory path to ifg files",
              "type": "string"
            }
          },
          "required": [
            "datalogger",
            "vertical_profiles",
            "interferograms"
          ]
        },
        "data_dst_dirs": {
          "title": "DataDstDirsConfig",
          "type": "object",
          "properties": {
            "results": {
              "title": "Results",
              "description": "directory path to results",
              "type": "string"
            }
          },
          "required": [
            "results"
          ]
        }
      },
      "required": [
        "location_data",
        "data_src_dirs",
        "data_dst_dirs"
      ]
    },
    "VerticalProfilesFTPServerConfig": {
      "title": "VerticalProfilesFTPServerConfig",
      "description": "Settings for accessing the ccycle ftp server. Besides the\n`email` field, these can be left as default in most cases.",
      "type": "object",
      "properties": {
        "email": {
          "title": "Email",
          "description": "email address to use to log in to the ccycle ftp server",
          "minLength": 3,
          "type": "string"
        },
        "max_day_delay": {
          "title": "Max Day Delay",
          "description": "maximum number of days of data availability delay of the ccycle ftp server. For example, on day 20 with `max delay = 7` the server should have data up to at least day 13. This is necessary because when requesting data from day 1-20 the output file might be names `day_1_13.tar` or `day_1_14.tar` -> with a delay of 7 days, the download process does not look for possible files named `day_1_12.tar`, `day_1_11.tar.`, etc.",
          "default": 7,
          "minimum": 0,
          "maximum": 10,
          "type": "integer"
        },
        "upload_sleep": {
          "title": "Upload Sleep",
          "description": "TODO",
          "default": 60,
          "minimum": 0,
          "type": "integer"
        },
        "upload_timeout": {
          "title": "Upload Timeout",
          "description": "TODO",
          "default": 180,
          "minimum": 0,
          "type": "integer"
        },
        "download_sleep": {
          "title": "Download Sleep",
          "description": "TODO",
          "default": 60,
          "minimum": 0,
          "type": "integer"
        },
        "download_timeout": {
          "title": "Download Timeout",
          "description": "in seconds, how long to wait for a `.tar` file to be generated before aborting the download",
          "default": 600,
          "minimum": 0,
          "type": "integer"
        }
      },
      "required": [
        "email"
      ]
    },
    "VerticalProfilesRequestScopeConfig": {
      "title": "VerticalProfilesRequestScopeConfig",
      "type": "object",
      "properties": {
        "from_date": {
          "title": "From Date",
          "description": "date string in format `YYYYMMDD` from which to request vertical profile data",
          "default": "19000101",
          "type": "string"
        },
        "to_date": {
          "title": "To Date",
          "description": "date string in format `YYYYMMDD` until which to request vertical profile data",
          "default": "21000101",
          "type": "string"
        },
        "data_types": {
          "title": "Data Types",
          "description": "list of data types to request from the ccycle ftp server",
          "default": [
            "GGG2014",
            "GGG2020"
          ],
          "minItems": 1,
          "type": "array",
          "items": {
            "enum": [
              "GGG2014",
              "GGG2020"
            ],
            "type": "string"
          }
        }
      }
    },
    "VerticalProfilesConfig": {
      "title": "VerticalProfilesConfig",
      "description": "Settings for vertical profiles retrieval. If `null`, the vertical profiles script will stop and log a warning",
      "type": "object",
      "properties": {
        "ftp_server": {
          "title": "VerticalProfilesFTPServerConfig",
          "description": "Settings for accessing the ccycle ftp server. Besides the\n`email` field, these can be left as default in most cases.",
          "type": "object",
          "properties": {
            "email": {
              "title": "Email",
              "description": "email address to use to log in to the ccycle ftp server",
              "minLength": 3,
              "type": "string"
            },
            "max_day_delay": {
              "title": "Max Day Delay",
              "description": "maximum number of days of data availability delay of the ccycle ftp server. For example, on day 20 with `max delay = 7` the server should have data up to at least day 13. This is necessary because when requesting data from day 1-20 the output file might be names `day_1_13.tar` or `day_1_14.tar` -> with a delay of 7 days, the download process does not look for possible files named `day_1_12.tar`, `day_1_11.tar.`, etc.",
              "default": 7,
              "minimum": 0,
              "maximum": 10,
              "type": "integer"
            },
            "upload_sleep": {
              "title": "Upload Sleep",
              "description": "TODO",
              "default": 60,
              "minimum": 0,
              "type": "integer"
            },
            "upload_timeout": {
              "title": "Upload Timeout",
              "description": "TODO",
              "default": 180,
              "minimum": 0,
              "type": "integer"
            },
            "download_sleep": {
              "title": "Download Sleep",
              "description": "TODO",
              "default": 60,
              "minimum": 0,
              "type": "integer"
            },
            "download_timeout": {
              "title": "Download Timeout",
              "description": "in seconds, how long to wait for a `.tar` file to be generated before aborting the download",
              "default": 600,
              "minimum": 0,
              "type": "integer"
            }
          },
          "required": [
            "email"
          ]
        },
        "request_scope": {
          "title": "VerticalProfilesRequestScopeConfig",
          "type": "object",
          "properties": {
            "from_date": {
              "title": "From Date",
              "description": "date string in format `YYYYMMDD` from which to request vertical profile data",
              "default": "19000101",
              "type": "string"
            },
            "to_date": {
              "title": "To Date",
              "description": "date string in format `YYYYMMDD` until which to request vertical profile data",
              "default": "21000101",
              "type": "string"
            },
            "data_types": {
              "title": "Data Types",
              "description": "list of data types to request from the ccycle ftp server",
              "default": [
                "GGG2014",
                "GGG2020"
              ],
              "minItems": 1,
              "type": "array",
              "items": {
                "enum": [
                  "GGG2014",
                  "GGG2020"
                ],
                "type": "string"
              }
            }
          }
        }
      },
      "required": [
        "ftp_server",
        "request_scope"
      ]
    },
    "AutomatedProffastGeneralConfig": {
      "title": "AutomatedProffastGeneralConfig",
      "type": "object",
      "properties": {
        "max_core_count": {
          "title": "Max Core Count",
          "description": "How many cores to use for parallel processing. There will be one process per sensor-day.",
          "default": 1,
          "minimum": 1,
          "maximum": 64,
          "type": "integer"
        },
        "ifg_file_regex": {
          "title": "Ifg File Regex",
          "description": "A regex string to match the ifg file names. In this string, `$(SENSOR_ID)` and `$(DATE)` are placeholders for the sensor id and the date of the ifg file.",
          "default": "^$(SENSOR_ID)$(DATE).*\\.\\d+$",
          "minLength": 1,
          "type": "string"
        }
      }
    },
    "AutomatedProffastDataSourcesConfig": {
      "title": "AutomatedProffastDataSourcesConfig",
      "description": "Which data sources to use (storage/manual queue)",
      "type": "object",
      "properties": {
        "storage": {
          "title": "Storage",
          "description": "Whether to use the storage data. Run every sensor-day, where there is input data (`config.data_src_dirs.interferograms`) but no output data (`config.data_dst_dirs.results`).",
          "default": true,
          "type": "boolean"
        },
        "manual_queue": {
          "title": "Manual Queue",
          "description": "Whether to use the manual queue. Compute a sensor-day if data is available at `config.data_src_dirs.interferograms`, independently of results-existence. Will overwrite existing results.",
          "default": true,
          "type": "boolean"
        }
      }
    },
    "AutomatedProffastModifiedIfgFilePermissionsConfig": {
      "title": "AutomatedProffastModifiedIfgFilePermissionsConfig",
      "type": "object",
      "properties": {
        "during_processing": {
          "title": "During Processing",
          "description": "A unix-like file permission string, e.g. `rwxr-xr-x`. This can be used to make the ifg files read-only during processing, to avoid accidental modification. Only used if not `null`.",
          "pattern": "^((r|-)(w|-)(x|-)){3}$",
          "type": "string"
        },
        "after_processing": {
          "title": "After Processing",
          "description": "A unix-like file permission string, e.g. `rwxr-xr-x`. Same as `during_processing`, but restoring the permissions after processing. Only used if not `null`.",
          "pattern": "^((r|-)(w|-)(x|-)){3}$",
          "type": "string"
        }
      }
    },
    "AutomatedProffastStorageDataFilterConfig": {
      "title": "AutomatedProffastStorageDataFilterConfig",
      "description": "Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`.",
      "type": "object",
      "properties": {
        "sensor_ids_to_consider": {
          "title": "Sensor Ids To Consider",
          "description": "Sensor ids to consider in the retrieval",
          "minItems": 1,
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "from_date": {
          "title": "From Date",
          "description": "Date string in format `YYYYMMDD` from which to consider data in the storage directory",
          "default": "19000101",
          "type": "string"
        },
        "to_date": {
          "title": "To Date",
          "description": "Date string in format `YYYYMMDD` until which to consider data in the storage directory",
          "default": "21000101",
          "type": "string"
        },
        "min_days_delay": {
          "title": "Min Days Delay",
          "description": "Minimum numbers of days to wait until processing. E.g. the vertical profiles from ccyle are available with a delay of 5 days, so it doesn't make sence to try processing earlier and get a lot of error messages because of missing vertical profiles.",
          "default": 5,
          "minimum": 0,
          "maximum": 60,
          "type": "integer"
        }
      },
      "required": [
        "sensor_ids_to_consider"
      ]
    },
    "AutomatedProffastConfig": {
      "title": "AutomatedProffastConfig",
      "description": "Settings for automated proffast processing. If `null`, the automated proffast script will stop and log a warning",
      "type": "object",
      "properties": {
        "general": {
          "title": "AutomatedProffastGeneralConfig",
          "type": "object",
          "properties": {
            "max_core_count": {
              "title": "Max Core Count",
              "description": "How many cores to use for parallel processing. There will be one process per sensor-day.",
              "default": 1,
              "minimum": 1,
              "maximum": 64,
              "type": "integer"
            },
            "ifg_file_regex": {
              "title": "Ifg File Regex",
              "description": "A regex string to match the ifg file names. In this string, `$(SENSOR_ID)` and `$(DATE)` are placeholders for the sensor id and the date of the ifg file.",
              "default": "^$(SENSOR_ID)$(DATE).*\\.\\d+$",
              "minLength": 1,
              "type": "string"
            }
          }
        },
        "data_sources": {
          "title": "AutomatedProffastDataSourcesConfig",
          "description": "Which data sources to use (storage/manual queue)",
          "type": "object",
          "properties": {
            "storage": {
              "title": "Storage",
              "description": "Whether to use the storage data. Run every sensor-day, where there is input data (`config.data_src_dirs.interferograms`) but no output data (`config.data_dst_dirs.results`).",
              "default": true,
              "type": "boolean"
            },
            "manual_queue": {
              "title": "Manual Queue",
              "description": "Whether to use the manual queue. Compute a sensor-day if data is available at `config.data_src_dirs.interferograms`, independently of results-existence. Will overwrite existing results.",
              "default": true,
              "type": "boolean"
            }
          }
        },
        "modified_ifg_file_permissions": {
          "title": "AutomatedProffastModifiedIfgFilePermissionsConfig",
          "type": "object",
          "properties": {
            "during_processing": {
              "title": "During Processing",
              "description": "A unix-like file permission string, e.g. `rwxr-xr-x`. This can be used to make the ifg files read-only during processing, to avoid accidental modification. Only used if not `null`.",
              "pattern": "^((r|-)(w|-)(x|-)){3}$",
              "type": "string"
            },
            "after_processing": {
              "title": "After Processing",
              "description": "A unix-like file permission string, e.g. `rwxr-xr-x`. Same as `during_processing`, but restoring the permissions after processing. Only used if not `null`.",
              "pattern": "^((r|-)(w|-)(x|-)){3}$",
              "type": "string"
            }
          }
        },
        "storage_data_filter": {
          "title": "AutomatedProffastStorageDataFilterConfig",
          "description": "Settings for filtering the storage data. Only used if `config.data_sources.storage` is `true`.",
          "type": "object",
          "properties": {
            "sensor_ids_to_consider": {
              "title": "Sensor Ids To Consider",
              "description": "Sensor ids to consider in the retrieval",
              "minItems": 1,
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "from_date": {
              "title": "From Date",
              "description": "Date string in format `YYYYMMDD` from which to consider data in the storage directory",
              "default": "19000101",
              "type": "string"
            },
            "to_date": {
              "title": "To Date",
              "description": "Date string in format `YYYYMMDD` until which to consider data in the storage directory",
              "default": "21000101",
              "type": "string"
            },
            "min_days_delay": {
              "title": "Min Days Delay",
              "description": "Minimum numbers of days to wait until processing. E.g. the vertical profiles from ccyle are available with a delay of 5 days, so it doesn't make sence to try processing earlier and get a lot of error messages because of missing vertical profiles.",
              "default": 5,
              "minimum": 0,
              "maximum": 60,
              "type": "integer"
            }
          },
          "required": [
            "sensor_ids_to_consider"
          ]
        }
      },
      "required": [
        "general",
        "data_sources",
        "modified_ifg_file_permissions",
        "storage_data_filter"
      ]
    },
    "OutputMergingTargetConfig": {
      "title": "OutputMergingTargetConfig",
      "type": "object",
      "properties": {
        "campaign_id": {
          "title": "Campaign Id",
          "description": "Campaign specified in location metadata.",
          "type": "string"
        },
        "sampling_rate": {
          "title": "Sampling Rate",
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
          "type": "string"
        },
        "dst_dir": {
          "title": "Dst Dir",
          "description": "Directory to write the output to.",
          "type": "string"
        },
        "data_types": {
          "title": "Data Types",
          "description": "Data columns to keep in the merged output files. The columns will be prefixed with the sensor id, i.e. `$(SENSOR_ID)_$(COLUMN_NAME)`.",
          "default": [
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
          "minItems": 1,
          "type": "array",
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
          }
        },
        "max_interpolation_gap_seconds": {
          "title": "Max Interpolation Gap Seconds",
          "description": "Maximum gap in seconds to interpolate over.",
          "default": 180,
          "minimum": 6,
          "maximum": 43200,
          "type": "integer"
        }
      },
      "required": [
        "campaign_id",
        "sampling_rate",
        "dst_dir"
      ]
    }
  }
};

export default CONFIG_SCHEMA_OBJECT;