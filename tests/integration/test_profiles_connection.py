import pytest
import ftplib

import src
from src import utils

@pytest.mark.order(3)
@pytest.mark.integration
def test_profiles_connection() -> None:
    config_path = utils.environment.get_config_path()
    config = src.types.Config.load(config_path)
    if config.profiles is None:
        return
    with ftplib.FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.profiles.server.email,
        user="anonymous",
        timeout=60,
    ) as ftp:
        print(ftp.nlst("ginput-jobs"))
