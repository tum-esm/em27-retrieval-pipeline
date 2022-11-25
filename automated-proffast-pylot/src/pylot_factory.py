import importlib.util
import importlib
import os
import random
import shutil
from string import Template
import string
import subprocess
import uuid
import requests
import sys
import json
from src.utils import load_proffast_config
from src.utils.logger import Logger
from clint.textui import progress
from zipfile import ZipFile
from tqdm import tqdm
import checksumdir
import inspect


class PylotFactory:

    def __init__(self):
        # Load Config
        self.config = load_proffast_config()
        self.working_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "prfpylot")

        # Template relative module name for importing
        self.rel_module_name = Template('src.prfpylot.$path.prfpylot')

        self.main = os.path.join(self.working_dir, 'main')
        self.tag_file = os.path.join(self.working_dir, 'tag')
        self.containers = []

        if os.path.exists(self.working_dir) == False:
            os.makedirs(self.working_dir)
        self._verify_main_pylot()       # import version of Pylot for this container
        print(f"setup prfpylot at {self.main} successfuly")

        Pylot_instance = self.import_pylot('main', tag=True)
        print(f"Main Pylot instance {Pylot_instance}")

    def create_pylot_instance(self):
        self._verify_main_pylot()
        container_id = PylotFactory.get_random_string(10)
        # Create new prfpylot instance
        shutil.copytree(self.main, os.path.join(self.working_dir, container_id))
        return self.import_pylot(container_id=container_id)


    def import_pylot(self, container_id, tag=False):
        MODULE_PATH = os.path.join(self.working_dir, container_id, "prfpylot", "__init__.py")
        MODULE_NAME = "prfpylot"
        # Create spec for module
        spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
        prfpylot = importlib.util.module_from_spec(spec)

        sys.modules[MODULE_NAME] = prfpylot
        spec.loader.exec_module(prfpylot)
        rel_module_name = self.rel_module_name.substitute(path=container_id)
        sys.modules[rel_module_name] = prfpylot
        print(f"importing pylot from {prfpylot.__file__}")
        try:
            from prfpylot.pylot import Pylot
            if tag:
                self.tag()
            print(inspect.getmodule(Pylot).__file__)
            return Pylot
        except ImportError as e:
            print("Unable to import pylot", e)
        return None 

    def _verify_main_pylot(self):
        if os.path.exists(self.tag_file) and os.path.exists(self.main):
            hash = checksumdir.dirhash(self.main)
            with open(self.tag_file, 'r') as f:
                stored_hash = f.read()
                if hash == stored_hash:
                    Logger.info(
                        "no changes done to the main proffast pylot version")
                else:
                    Logger.error(
                        "Changes detected in the main proffast pylot version, creating fresh main instance")
                    shutil.rmtree(self.main)
                    self._clone_pylot_repo()
        else:
            self._clone_pylot_repo()

    def _clone_pylot_repo(self):
        """
        Clones the pylot repository. Stores a master copy in the folder self.master
        Do a shallow copy to reduce size.
        """
        Logger.info(f"Loading Proffast.. from {self.config['proffast_url']}")
        print(self.main)
        proffast_url = self.config['proffast_url']

        proffast_archive = os.path.join(self.working_dir, 'proffast.zip')
        r = requests.get(proffast_url, stream=True)
        with open(proffast_archive, 'wb') as f:
            total_length = int(r.headers.get('content-length'))
            for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1):
                if chunk:
                    f.write(chunk)
                    f.flush()

        with ZipFile(file=proffast_archive) as zip_file:
            for file in tqdm(iterable=zip_file.namelist(), total=len(zip_file.namelist())):
                zip_file.extract(member=file, path=self.main)

        os.remove(proffast_archive)
        ################# Done downloading everything ############################
        ################ Compiling code ##################################

        compile_script = self.config['compile_script']
        proffast_dir = os.path.join(self.main, 'prf')

        compilation = subprocess.run(
            ['bash', f'{compile_script}'], cwd=proffast_dir)
        if compilation.returncode == 0:
            Logger.info("Compiled proffast")
        
        compile_script = self.config['ifgs_compile_script']
        detect_corrupt_ifgs_dir = os.path.join(self.main, '..', '..', 'detect_corrupt_ifgs')

        compilation = subprocess.run(
            ['bash', f'{compile_script}'], cwd=detect_corrupt_ifgs_dir)
        if compilation.returncode == 0:
            Logger.info("Compiled Detect corrupt ifgs")
        

    def tag(self):  
        # Creating checksum.
        hash = checksumdir.dirhash(self.main)
        # Creating tag file.
        with open(self.tag_file, 'w') as tag_file:
            tag_file.write(hash)


    def get_random_string(length):
        # choose from all lowercase letter
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    def create(self):
        """
        Creates a copy of the main Pylot Proffast repository and returns a version of the Pylot class
        that is to be later instanciated by the consumer with config.
        """
        # Src: self.main
        # Destination: random id in the self.working_dir.
        pass