/* prettier-ignore */
const SENSORS_SCHEMA: any = {
    "items": {
        "description": "Metadata for a single sensor.",
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
                "deprecated": true,
                "items": {},
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