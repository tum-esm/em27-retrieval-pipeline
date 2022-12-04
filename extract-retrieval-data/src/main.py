from . import utils, procedures


def run() -> None:
    config = utils.load_config()

    campaign_stations = procedures.get_campaign_stations("sda")
