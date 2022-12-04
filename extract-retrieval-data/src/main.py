from . import utils, procedures


def run() -> None:
    config = utils.load_config()
    campaign_stations = procedures.get_campaign_stations(config.request.campaign_name)
    print(f"campaign_stations = {campaign_stations}\n")

    campaign_dates = procedures.get_campaign_dates(config.request.campaign_name)
    print(f"campaign_dates = {campaign_dates}\n")

    # TODO: for every date in campaign dates produce one CSV;
    #       all code below in this loop ("per CSV file"). Only
    #       dates between config.request.from_date and .to_date
    #       should be considered

    # for all stations that were at their correct location at
    # this date, query the database
    df = procedures.get_daily_dataframe(
        config.database, "2.2", ["ma", "mb"], "20210109"
    )
    # TODO: df does not have the same columns (should have all
    #       NaN columns for all stations of that campaign)

    print(df)
    df.to_csv("some.csv")
