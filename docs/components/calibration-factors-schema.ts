/* prettier-ignore */
const CALIBRATION_FACTORS_SCHEMA: any = {
    "items": {
        "properties": {
            "sensor_id": {
                "title": "Sensor Id",
                "type": "string"
            },
            "valid_from_datetime": {
                "format": "date-time",
                "title": "Valid From Datetime",
                "type": "string"
            },
            "valid_to_datetime": {
                "format": "date-time",
                "title": "Valid To Datetime",
                "type": "string"
            },
            "xco2": {
                "description": "Calibration factor for carbon dioxide: xco2_cal = xco2_raw * factor",
                "title": "Xco2",
                "type": "number"
            },
            "xch4": {
                "description": "Calibration factor for methane: xch4_cal = xch4_raw * factor",
                "title": "Xch4",
                "type": "number"
            },
            "xco": {
                "description": "Calibration factor for carbon monoxide: xco_cal = xco_raw * factor",
                "title": "Xco",
                "type": "number"
            },
            "xh2o": {
                "description": "Calibration factor for water vapor: xh2o_cal = xh2o_raw * factor",
                "title": "Xh2O",
                "type": "number"
            }
        },
        "required": [
            "sensor_id",
            "valid_from_datetime",
            "valid_to_datetime",
            "xco2",
            "xch4",
            "xco",
            "xh2o"
        ],
        "title": "CalibrationFactors",
        "type": "object"
    },
    "title": "CalibrationFactorsList",
    "type": "array"
};

export default CALIBRATION_FACTORS_SCHEMA;