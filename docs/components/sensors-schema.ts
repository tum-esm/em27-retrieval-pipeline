/* prettier-ignore */
const SENSORS_SCHEMA: any = {
    "items": {
        "description": "Metadata for a single sensor.\n\n`sensor_id`, `serial_number` and `locations` are required. The other items\n- `different_utc_offsets`, `different_pressure_data_sources` and \n`different_calibration_factors` - are only needed of they deviate from the\ndefault values (no UTC offset, pressure data source is \"built-in\" on,\nno calibration of pressure or output values).",
        "properties": {
            "sensor_id": {
                "description": "Your internal sensor ID identifying a specific EM27/SUN (system). Allowed characters: letters, numbers, dashes, underscores.",
                "maxLength": 128,
                "minLength": 1,
                "pattern": "^[a-zA-Z0-9_-]+$",
                "title": "Sensor Id",
                "type": "string"
            },
            "serial_number": {
                "description": "Serial number of the EM27/SUN",
                "minimum": 1,
                "title": "Serial Number",
                "type": "integer"
            },
            "setups": {
                "items": {
                    "description": "An element in the `sensor.setups` list",
                    "properties": {
                        "from_datetime": {
                            "format": "date-time",
                            "title": "From Datetime",
                            "type": "string"
                        },
                        "to_datetime": {
                            "format": "date-time",
                            "title": "To Datetime",
                            "type": "string"
                        },
                        "value": {
                            "properties": {
                                "location_id": {
                                    "description": "Location ID referring to a location named in `locations.json`",
                                    "minLength": 1,
                                    "title": "Location Id",
                                    "type": "string"
                                },
                                "pressure_data_source": {
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
                                    "description": "Pressure data source, if not set, using the pressure of the sensor",
                                    "title": "Pressure Data Source"
                                },
                                "utc_offset": {
                                    "default": 0,
                                    "description": "UTC offset of the location, if not set, using an offset of 0",
                                    "exclusiveMaximum": 12.0,
                                    "exclusiveMinimum": -12.0,
                                    "title": "Utc Offset",
                                    "type": "number"
                                },
                                "atmospheric_profile_location_id": {
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
                                    "description": "Location ID referring to a location named in `locations.json`. This location's coordinates are used for the atmospheric profiles in the retrieval.",
                                    "title": "Atmospheric Profile Location Id"
                                }
                            },
                            "required": [
                                "location_id"
                            ],
                            "title": "Setup",
                            "type": "object"
                        }
                    },
                    "required": [
                        "from_datetime",
                        "to_datetime",
                        "value"
                    ],
                    "title": "SetupsListItem",
                    "type": "object"
                },
                "minItems": 0,
                "title": "Setups",
                "type": "array"
            },
            "calibration_factors": {
                "default": [],
                "description": "List of calibration factors to used. Only required if thecalibration factor is not 1.0. The pressure calibration factor is applied before the retrieval, the other factors are applied to the results produced by Proffast/GFIT.",
                "items": {
                    "description": "An element in the `sensor.calibration_factors` list",
                    "properties": {
                        "from_datetime": {
                            "format": "date-time",
                            "title": "From Datetime",
                            "type": "string"
                        },
                        "to_datetime": {
                            "format": "date-time",
                            "title": "To Datetime",
                            "type": "string"
                        },
                        "value": {
                            "description": "These can be either single values to be applied by\nmultiplication/division or a list of values for example\nfor one airmass-independent and one airmass-dependent\nfactor (see Ohyama 2021).",
                            "properties": {
                                "pressure": {
                                    "default": 1,
                                    "description": "Pressure calibration factor. estimate = measured * factor",
                                    "title": "Pressure",
                                    "type": "number"
                                },
                                "xco2": {
                                    "allOf": [
                                        {
                                            "properties": {
                                                "factors": {
                                                    "default": [
                                                        1
                                                    ],
                                                    "description": "List of calibration factors. The scheme defines how to use them.",
                                                    "items": {
                                                        "type": "number"
                                                    },
                                                    "title": "Factors",
                                                    "type": "array"
                                                },
                                                "scheme": {
                                                    "anyOf": [
                                                        {
                                                            "type": "string"
                                                        },
                                                        {
                                                            "type": "null"
                                                        }
                                                    ],
                                                    "default": null,
                                                    "description": "Used calibration scheme - for example \"Ohyama 2021\". This can be an arbitrary string or `null`.",
                                                    "title": "Scheme"
                                                },
                                                "note": {
                                                    "anyOf": [
                                                        {
                                                            "type": "string"
                                                        },
                                                        {
                                                            "type": "null"
                                                        }
                                                    ],
                                                    "default": null,
                                                    "description": "Optional note, e.g. \"actual = factors[0] * measured + factors[1]\"",
                                                    "title": "Note"
                                                }
                                            },
                                            "title": "GasSpecificCalibrationFactors",
                                            "type": "object"
                                        }
                                    ],
                                    "default": {
                                        "factors": [
                                            1.0
                                        ],
                                        "scheme": null,
                                        "note": null
                                    }
                                },
                                "xch4": {
                                    "allOf": [
                                        {
                                            "properties": {
                                                "factors": {
                                                    "default": [
                                                        1
                                                    ],
                                                    "description": "List of calibration factors. The scheme defines how to use them.",
                                                    "items": {
                                                        "type": "number"
                                                    },
                                                    "title": "Factors",
                                                    "type": "array"
                                                },
                                                "scheme": {
                                                    "anyOf": [
                                                        {
                                                            "type": "string"
                                                        },
                                                        {
                                                            "type": "null"
                                                        }
                                                    ],
                                                    "default": null,
                                                    "description": "Used calibration scheme - for example \"Ohyama 2021\". This can be an arbitrary string or `null`.",
                                                    "title": "Scheme"
                                                },
                                                "note": {
                                                    "anyOf": [
                                                        {
                                                            "type": "string"
                                                        },
                                                        {
                                                            "type": "null"
                                                        }
                                                    ],
                                                    "default": null,
                                                    "description": "Optional note, e.g. \"actual = factors[0] * measured + factors[1]\"",
                                                    "title": "Note"
                                                }
                                            },
                                            "title": "GasSpecificCalibrationFactors",
                                            "type": "object"
                                        }
                                    ],
                                    "default": {
                                        "factors": [
                                            1.0
                                        ],
                                        "scheme": null,
                                        "note": null
                                    }
                                },
                                "xco": {
                                    "allOf": [
                                        {
                                            "properties": {
                                                "factors": {
                                                    "default": [
                                                        1
                                                    ],
                                                    "description": "List of calibration factors. The scheme defines how to use them.",
                                                    "items": {
                                                        "type": "number"
                                                    },
                                                    "title": "Factors",
                                                    "type": "array"
                                                },
                                                "scheme": {
                                                    "anyOf": [
                                                        {
                                                            "type": "string"
                                                        },
                                                        {
                                                            "type": "null"
                                                        }
                                                    ],
                                                    "default": null,
                                                    "description": "Used calibration scheme - for example \"Ohyama 2021\". This can be an arbitrary string or `null`.",
                                                    "title": "Scheme"
                                                },
                                                "note": {
                                                    "anyOf": [
                                                        {
                                                            "type": "string"
                                                        },
                                                        {
                                                            "type": "null"
                                                        }
                                                    ],
                                                    "default": null,
                                                    "description": "Optional note, e.g. \"actual = factors[0] * measured + factors[1]\"",
                                                    "title": "Note"
                                                }
                                            },
                                            "title": "GasSpecificCalibrationFactors",
                                            "type": "object"
                                        }
                                    ],
                                    "default": {
                                        "factors": [
                                            1.0
                                        ],
                                        "scheme": null,
                                        "note": null
                                    }
                                }
                            },
                            "title": "CalibrationFactors",
                            "type": "object"
                        }
                    },
                    "required": [
                        "from_datetime",
                        "to_datetime",
                        "value"
                    ],
                    "title": "CalibrationFactorsListItem",
                    "type": "object"
                },
                "title": "Calibration Factors",
                "type": "array"
            }
        },
        "required": [
            "sensor_id",
            "serial_number",
            "setups"
        ],
        "title": "SensorMetadata",
        "type": "object"
    },
    "title": "SensorMetadataList",
    "type": "array"
};

export default SENSORS_SCHEMA;