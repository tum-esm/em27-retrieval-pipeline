"""Download_example is a module of PROFFASTpylot.

Download the Sodankyla example data from the KIT website.

License information:
PROFFASTpylot - Running PROFFAST with Python
Copyright (C)   2022    Lena Feld, Benedikt Herkommer, 
                        Karlsruhe Institut of Technology (KIT)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3 as published by
the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
from tqdm import tqdm
from zipfile import ZipFile
import os
import sys


class ExampleDownloadHandler:
    """Check if the example data is available in the installation path
    of PROFFASTpylot and downloads it if not.
    """
    def __init__(self):
        self.scriptpath = os.path.abspath(os.path.dirname(__file__))
        self.example_path = os.path.join(self.scriptpath, "..", "example")
        self.example_path = os.path.abspath(self.example_path)

    def download_example_data(self):
        """ Download and extract the example data. """
        # Code for download copied from here:
        # https://www.simplifiedpython.net/python-download-file/
        url = (
            "https://www.imk-asf.kit.edu/downloads/"
            "Coccon-SW/example_data_sodankyla.zip")
        req = requests.get(url, stream=True)
        total_size = int(req.headers['content-length'])

        # Download the data
        target_file = os.path.join(self.scriptpath, "example_data_temp.zip")
        chunk_size = 1024
        with open(target_file, "wb") as file:
            for data in tqdm(
                    iterable=req.iter_content(chunk_size=chunk_size),
                    total=total_size/chunk_size, unit='KB'):
                file.write(data)

        # Extract it
        with ZipFile(target_file, 'r') as file:
            file.extractall(os.path.join(self.example_path, "input_data"))
        # delete the downloaded zip file:
        os.remove(target_file)
        print("Download Completed")

    def check_and_download_example_data(self):
        """Check if example data is available and download it."""

        input_data_path = os.path.join(self.example_path, "input_data")
        if os.path.exists(input_data_path):
            print("Example data are already available on disk")
            return
        else:
            print("Example data where not found on disk.")
            print("Do you like to download them? This will download 104 MB of"
                  " data to your disk.")
            dec = input("Enter 'yes' to download the data or 'no' to abort:\n")
            while True:
                if dec == 'no':
                    sys.exit(0)
                    return
                elif dec == 'yes':
                    break
                else:
                    dec = input("Could not parse input."
                                " Enter 'yes' or 'no':\n")
            self.download_example_data()
