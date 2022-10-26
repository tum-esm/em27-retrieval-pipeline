import os
import json
import logging
import getpass

import keyring
import requests

import subprocess
from pathlib import Path
from typing import Callable

from filelock import FileLock

from src import interfaces, utils, types

# TODO - Logger, IO Type, LockLogging

def run() -> None:

    logging.basicConfig(level=logging.INFO)
    
    try:

        project_path = Path(os.path.abspath(__file__)).parent

        # Load and validate the configuration
        config_path = os.path.join(project_path, "config", "config.json")
        with FileLock(config_path + ".lock", timeout=10), open(config_path, "r") as f:
            config = types.Configuration(**json.load(f))
            logging.info(f"Configuration loaded {config}")
            

        # Check for git credentials
        service = "download_vertical_profiles"

        """Security Considerations keyring
        macOS: Any Python script or application can access secrets created by keyring from that same
        Python executable without the operating system prompting the user for a password.
        To cause any specific secret to prompt for a password every time it is accessed,
        locate the credential using the Keychain Access application, and in the Access Control settings,
        remove Python from the list of allowed applications.
        https://keyring.readthedocs.io/en/latest/#security-considerations
        Installation: https://github.com/jaraco/keyring
        #NOTE - OAuth(?)
        """

        git_username = keyring.get_password(service, "git_username")
        git_token = keyring.get_password(service, "git_token")
        override = False #FIXME

        if git_username is None or git_token is None or override:
            git_username = input("GIT_USERNAME: ")
            git_token = getpass.getpass("GIT_TOKEN: ")
            keyring.set_password(service, "git_username", git_username)
            keyring.set_password(service, "git_token", git_token)

        # Load the locations
        response = requests.get(
            config.location_data, auth=(git_username, git_token), timeout=10
        )
        # Check for bad requests
        response.raise_for_status()
        logging.info(f"Locations loaded {response.text}")
        

    except Exception as e:
        print(e)

if __name__ == "__main__":
    run()
