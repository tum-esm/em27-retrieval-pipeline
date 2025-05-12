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
                "maximum": 180,
                "minimum": -180,
                "title": "Lon",
                "type": "number"
            },
            "lat": {
                "maximum": 90,
                "minimum": -90,
                "title": "Lat",
                "type": "number"
            },
            "alt": {
                "maximum": 10000,
                "minimum": -20,
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