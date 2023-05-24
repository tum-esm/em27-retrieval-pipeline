/* prettier-ignore */
const MANUAL_QUEUE_SCHEMA_OBJECT: any = {
  "title": "ManualQueue",
  "type": "object",
  "properties": {
    "items": {
      "title": "Items",
      "default": [],
      "type": "array",
      "items": {
        "title": "ManualQueueItem",
        "type": "object",
        "properties": {
          "sensor_id": {
            "title": "Sensor Id",
            "type": "string"
          },
          "date": {
            "title": "Date",
            "description": "Date in YYYYMMDD format",
            "type": "string"
          },
          "priority": {
            "title": "Priority",
            "description": "Priority of the item. Cannot be zero. Items with higher priority are processed first. If data from both the storage queue and the manual queue are considered, the storage queue items have a priority of zero.",
            "minimum": 1,
            "type": "integer"
          }
        },
        "required": [
          "sensor_id",
          "date",
          "priority"
        ]
      }
    }
  },
  "definitions": {
    "ManualQueueItem": {
      "title": "ManualQueueItem",
      "type": "object",
      "properties": {
        "sensor_id": {
          "title": "Sensor Id",
          "type": "string"
        },
        "date": {
          "title": "Date",
          "description": "Date in YYYYMMDD format",
          "type": "string"
        },
        "priority": {
          "title": "Priority",
          "description": "Priority of the item. Cannot be zero. Items with higher priority are processed first. If data from both the storage queue and the manual queue are considered, the storage queue items have a priority of zero.",
          "minimum": 1,
          "type": "integer"
        }
      },
      "required": [
        "sensor_id",
        "date",
        "priority"
      ]
    }
  }
};

export default MANUAL_QUEUE_SCHEMA_OBJECT;