/* prettier-ignore */
const LOCATIONS_SCHEMA: any = {
    "items": {
        "properties": {
            "location_id": {
                "description": "Your internal location ID identifying a specific location. Allowed values: letters, numbers, dashes, underscores.",
                "maxLength": 128,
                "minLength": 1,
                "pattern": "^[a-zA-Z0-9_-]+$",
                "title": "Location Id",
                "type": "string"
            },
            "details": {
                "default": "",
                "minLength": 0,
                "title": "Details",
                "type": "string"
            },
            "lon": {
                "maximum": 180.0,
                "minimum": -180.0,
                "title": "Lon",
                "type": "number"
            },
            "lat": {
                "maximum": 90.0,
                "minimum": -90.0,
                "title": "Lat",
                "type": "number"
            },
            "alt": {
                "maximum": 10000.0,
                "minimum": -20.0,
                "title": "Alt",
                "type": "number"
            }
        },
        "required": [
            "location_id",
            "lon",
            "lat",
            "alt"
        ],
        "title": "LocationMetadata",
        "type": "object"
    },
    "title": "LocationMetadataList",
    "type": "array"
};

export default LOCATIONS_SCHEMA;