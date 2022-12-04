from . import utils, procedures


def run() -> None:
    config = utils.load_config()
    campaign_stations = procedures.get_campaign_stations(config.request.campaign_name)
    campaign_dates = procedures.get_campaign_dates(config.request.campaign_name)
    print(campaign_stations)
    print(campaign_dates)

    df = procedures.get_daily_dataframe(
        config.database, "2.2", ["ma", "mb"], "20210109"
    )
    print(df)
    df.to_csv("some.csv")
