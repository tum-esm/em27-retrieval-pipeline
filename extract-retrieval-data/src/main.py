from . import utils, procedures


def run() -> None:
    config = utils.load_config()
    campaign_stations = procedures.get_campaign_stations(config.request.campaign_name)
    campaign_dates = procedures.get_campaign_dates(config.request.campaign_name)
    print(campaign_stations)
    print(campaign_dates)

    procedures.get_raw_station_data(config.database, "2.2", "ma", "20210109")
