import importlib
import os
import random
import shutil
import string
import subprocess
import requests
from src.utils import load_proffast_config
from src import proffast_path
from src.utils.logger import Logger
from clint.textui import progress
from zipfile import ZipFile
from tqdm import tqdm
import checksumdir


class PylotFactory:

    config = {}
    container_runner = ""
    main = ""
    tag_file = ""
    containers = {}
    logger = None

    def __init__(self, logger: Logger):
        # Load Config
        self.config = load_proffast_config()
        self.container_runner = self.config["container_runner"]
        self.logger = logger
        self.main = os.path.join(proffast_path, "main")
        self.containers = {}

        if os.path.exists(self.main) and len(os.listdir(self.main)) > 0:
            self._verify_main_pylot()  # import version of Pylot for this container
        else:
            logger.error(
                "Pylot submodule not initialized. please setup submodule and rerun"
            )
            raise RuntimeError("Pylot submodule not initialized")
        print(f"setup prfpylot at {self.main} successfuly")

    def create_pylot_instance(self) -> str:
        # self._verify_main_pylot()
        # Generate random container_id
        container_id = PylotFactory.get_random_string(10)
        container_path = os.path.join(proffast_path, container_id)
        # Create new prfpylot instance
        shutil.copytree(self.main, container_path)
        # Register Container
        self.containers[container_id] = container_path

        return container_id

    def execute_pylot(
        self, container_id: str, config_path: str, num_threads: int
    ) -> subprocess.CompletedProcess:
        # Do we need a timeout?
        runner = os.path.join(proffast_path, self.container_runner)
        result = subprocess.run(
            ["python", runner, container_id, config_path, str(num_threads)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result

    def clean_up(self) -> None:
        for _, item in self.containers.items():
            shutil.rmtree(item)

    def _verify_main_pylot(self):
        if os.path.exists(os.path.join(self.main, "prf")):
            self.logger.info("Proffast setup, continuing program")
        else:
            self._clone_pylot_repo()

    def _clone_pylot_repo(self):
        """
        Clones the pylot repository. Stores a master copy in the folder self.master
        Do a shallow copy to reduce size.
        """
        self.logger.info(f"Loading Proffast.. from {self.config['proffast_url']}")
        proffast_url = self.config["proffast_url"]

        proffast_archive = os.path.join(self.main, "proffast.zip")
        r = requests.get(proffast_url, stream=True)
        with open(proffast_archive, "wb") as f:
            total_length = int(r.headers.get("content-length"))
            for chunk in progress.bar(
                r.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1
            ):
                if chunk:
                    f.write(chunk)
                    f.flush()

        with ZipFile(file=proffast_archive) as zip_file:
            for file in tqdm(
                iterable=zip_file.namelist(), total=len(zip_file.namelist())
            ):
                zip_file.extract(member=file, path=self.main)

        os.remove(proffast_archive)
        ################# Done downloading everything ############################
        ################ Compiling code ##################################

        compile_script = self.config["compile_script"]
        proffast_dir = os.path.join(self.main, "prf")

        compilation = subprocess.run(["bash", f"{compile_script}"], cwd=proffast_dir)
        if compilation.returncode == 0:
            self.logger.info("Compiled proffast")

        compile_script = self.config["ifgs_compile_script"]
        detect_corrupt_ifgs_dir = os.path.join(
            self.main, "..", "..", "detect_corrupt_ifgs"
        )

        compilation = subprocess.run(
            ["bash", f"{compile_script}"], cwd=detect_corrupt_ifgs_dir
        )
        if compilation.returncode == 0:
            self.logger.info("Compiled Detect corrupt ifgs")

    def tag(self):
        # Creating checksum.
        hash = checksumdir.dirhash(self.main)
        # Creating tag file.
        with open(self.tag_file, "w") as tag_file:
            tag_file.write(hash)

    @staticmethod
    def get_random_string(length):
        # choose from all lowercase letter
        letters = string.ascii_lowercase
        result_str = "".join(random.choice(letters) for i in range(length))
        return result_str
