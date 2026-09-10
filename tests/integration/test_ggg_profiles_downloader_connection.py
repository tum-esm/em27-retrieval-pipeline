import pytest
import ftplib

import src


@pytest.mark.order(3)
@pytest.mark.integration
def test_profiles_connection() -> None:
    config = src.types.Config.load()
    if config.ggg_profiles_downloader is None:
        return
    with ftplib.FTP(
        host="ccycle.gps.caltech.edu",
        passwd=config.ggg_profiles_downloader.server.email,
        user="anonymous",
        timeout=60,
    ) as ftp:
        print(ftp.nlst("ginput-jobs"))
