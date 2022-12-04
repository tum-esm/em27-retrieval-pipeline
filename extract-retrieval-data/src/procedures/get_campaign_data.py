from src import custom_types

# 1. Download the campaigns.json file
# 2. Raise Exception if the requested campaign doesn't exist
# 3. Return a dict of dates with a list of sensors for each day


def get_campaign_sensors(
    campaign_name: str,
) -> list[custom_types.CampaignSensor]:
    # 1. Download the campaigns.json file
    # 3. Return a dict of dates with a list of sensors for each day

    return [
        custom_types.CampaignSensor(
            **{
                "station_id": "ma",
                "default_location": "TUM_I",
                "direction": "center",
                "lat": 0.0,
                "lon": 0.0,
            }
        ),
        custom_types.CampaignSensor(
            **{
                "station_id": "mb",
                "default_location": "FEL",
                "direction": "east",
                "lat": 0.0,
                "lon": 0.0,
            }
        ),
    ]


def get_campaign_dates(
    campaign_name: str,
) -> dict[custom_types.Date, list[custom_types.StationId]]:
    # 1. Download the campaigns.json file
    # 2. Raise Exception if the requested campaign doesn't exist
    # 3. Return a dict of dates with a list of sensors for each day

    return {
        "20220101": ["ma"],
        "20220102": ["ma", "mb"],
        "20220104": ["mb"],
    }
