import pytest
import ftplib
import os
import warnings
import tum_esm_utils
from src.utils.files import read_yaml
import src


@pytest.mark.order(3)
@pytest.mark.integration
def test_profiles_connection() -> None:
    config_setup = read_yaml(tum_esm_utils.files.rel_to_abs_path("../../config_setup.yml"))
    if config_setup['alternate_config_dir'] is None:
        config_path = None # default config path
    else:
        config_path = os.path.join(config_setup["alternate_config_dir"], "config.json")
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
