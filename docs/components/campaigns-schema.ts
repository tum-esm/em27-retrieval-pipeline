/* prettier-ignore */
const CAMPAIGNS_SCHEMA: any = {
    "default": [],
    "items": {
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
            "campaign_id": {
                "description": "Your internal sensor ID identifying a specific campaign. Allowed values: letters, numbers, dashes, underscores.",
                "maxLength": 128,
                "minLength": 1,
                "pattern": "^[a-zA-Z0-9_-]+$",
                "title": "Campaign Id",
                "type": "string"
            },
            "sensor_ids": {
                "items": {
                    "type": "string"
                },
                "title": "Sensor Ids",
                "type": "array"
            },
            "location_ids": {
                "items": {
                    "type": "string"
                },
                "title": "Location Ids",
                "type": "array"
            }
        },
        "required": [
            "from_datetime",
            "to_datetime",
            "campaign_id",
            "sensor_ids",
            "location_ids"
        ],
        "title": "CampaignMetadata",
        "type": "object"
    },
    "title": "CampaignMetadataList",
    "type": "array"
};

export default CAMPAIGNS_SCHEMA;