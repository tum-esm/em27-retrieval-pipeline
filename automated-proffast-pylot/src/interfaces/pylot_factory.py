import os
import shutil
import subprocess
from src import utils
from src import proffast_path
from src.utils.logger import Logger


dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
PYLOT_ROOT_DIR = os.path.join(PROJECT_DIR, "src", "prfpylot")

EXECUTABLE_FILEPATHS = [
    os.path.join(PYLOT_ROOT_DIR, "main", "prf", "preprocess", "preprocess4"),
    os.path.join(PYLOT_ROOT_DIR, "main", "prf", "pcxs20"),
    os.path.join(PYLOT_ROOT_DIR, "main", "prf", "invers20"),
    os.path.join(PROJECT_DIR, "src", "detect_corrupt_ifgs", "parser", "ifg_parser"),
]


class PylotFactory:
    def __init__(self, logger: Logger):
        self.logger = logger

        ContainerId = str
        ContainerPath = str
        self.container_paths: dict[ContainerId, ContainerPath] = {}

        self._init_pylot_code()

        print(f"prfpylot of main copy successful")

    def create_pylot_instance(self) -> str:
        container_id = utils.get_random_string(
            length=10, forbidden=self.container_paths.keys()
        )
        container_path = os.path.join(proffast_path, container_id)

        self.containers[container_id] = container_path
        shutil.copytree(self.main, container_path)

        return container_id

    def execute_pylot(
        self,
        container_id: str,
        pylot_config_path: str,
    ) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [
                "python",
                os.path.join(PYLOT_ROOT_DIR, "run.py"),
                container_id,
                pylot_config_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result

    def remove_container(self, container_id: str) -> None:
        shutil.rmtree(self.containers[container_id])
        del self.containers[container_id]

    def remove_all_containers(self) -> None:
        for container_id in self.containers.keys():
            self.remove_container(container_id)

    def _init_pylot_code(self):
        if (not os.path.exists(self.main)) or (len(os.listdir(self.main)) == 0):
            raise RuntimeError("Pylot submodule not initialized")

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if not os.path.exists(os.path.join(self.main, "prf")):
            self.logger.info(f"downloading proffast code")

            KIT_BASE_URL = "wget https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
            ZIPFILE_NAME = "PROFFASTv2.2.zip"

            utils.run_shell_command(
                f"wget {KIT_BASE_URL}/{ZIPFILE_NAME}",
                working_directory=os.path.join(PYLOT_ROOT_DIR, "main"),
            )
            utils.run_shell_command(
                f"unzip {ZIPFILE_NAME}",
                working_directory=os.path.join(PYLOT_ROOT_DIR, "main"),
            )
            os.remove(os.path.join(PYLOT_ROOT_DIR, "main", ZIPFILE_NAME))

        # COMPILE FORTRAN CODE
        self.logger.info(f"compiling fortran code")

        for filepath in EXECUTABLE_FILEPATHS:
            if os.path.isfile(filepath):
                os.remove(filepath)

        utils.run_shell_command(
            f"bash install_proffast_linux.sh",
            working_directory=os.path.join(PYLOT_ROOT_DIR, "main", "prf"),
        )
        utils.run_shell_command(
            f"bash compile.sh",
            working_directory=os.path.join(PROJECT_DIR, "src", "detect_corrupt_ifgs"),
        )

        for filepath in EXECUTABLE_FILEPATHS:
            if os.path.isfile(filepath):
                raise FileNotFoundError(
                    f'file "{filepath}" does not exist after compilation'
                )

        self.logger.info(f"fortran compilation is done")
