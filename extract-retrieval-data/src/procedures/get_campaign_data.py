from src import custom_types


def get_campaign_stations(
    campaign_name: str,
) -> list[custom_types.CampaignStation]:
    # 1. Download the campaigns.json file
    # 3. Return a list of the campaigns sensors

    return [
        custom_types.CampaignStation(
            **{
                "station_id": "ma",
                "default_location": "TUM_I",
                "direction": "center",
                "details": "TUM Dach Innenstadt",
                "lon": 11.569,
                "lat": 48.151,
                "alt": 539,
            }
        ),
        custom_types.CampaignStation(
            **{
                "station_id": "mb",
                "default_location": "FEL",
                "direction": "east",
                "details": "Feldkirchen",
                "lon": 11.73,
                "lat": 48.148,
                "alt": 536,
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
