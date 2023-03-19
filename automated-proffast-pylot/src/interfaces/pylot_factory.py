import os
import shutil
from src import custom_types, utils
import tum_esm_utils

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
PYLOT_ROOT_DIR = os.path.join(PROJECT_DIR, "src", "prfpylot")
PYLOT_MAIN_CLONE_DIR = os.path.join(PYLOT_ROOT_DIR, "main")
KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
ZIPFILE_NAME = "PROFFASTv2.2.zip"


class PylotFactory:
    def __init__(self, logger: utils.Logger):
        self.logger = logger
        self.containers: list[custom_types.PylotContainer] = []
        self._init_pylot_code()
        self.logger.info("PylotFactory is set up")

    def create_container(self) -> custom_types.PylotContainer:
        container_id = tum_esm_utils.text.get_random_string(
            length=10, forbidden=[c.container_id for c in self.containers]
        )

        # copy container code and compile the fortran code
        container_path = os.path.join(
            PYLOT_ROOT_DIR,
            "containers",
            f"pylot-container-{container_id}",
        )
        shutil.copytree(PYLOT_MAIN_CLONE_DIR, container_path)
        tum_esm_utils.shell.run_shell_command(
            command=f"bash install_proffast_linux.sh",
            working_directory=os.path.join(container_path, "prf"),
        )

        # generate empty input directory
        data_input_path = os.path.join(
            PYLOT_ROOT_DIR,
            "containers",
            f"pylot-container-{container_id}-input",
        )
        os.mkdir(data_input_path)
        os.mkdir(os.path.join(data_input_path, "ifg"))
        os.mkdir(os.path.join(data_input_path, "map"))
        os.mkdir(os.path.join(data_input_path, "log"))

        # generate empty output directory
        data_output_path = os.path.join(
            PYLOT_ROOT_DIR,
            "containers",
            f"pylot-container-{container_id}-output",
        )
        os.mkdir(data_output_path)

        # bundle container paths together
        self.containers.append(
            custom_types.PylotContainer(
                container_id=container_id,
                container_path=container_path,
                data_input_path=data_input_path,
                data_output_path=data_output_path,
                pylot_config_path=os.path.join(data_input_path, "pylot_config.yml"),
                pylot_log_format_path=os.path.join(
                    data_input_path, "pylot_log_format.yml"
                ),
            )
        )

        return self.containers[-1]

    def remove_container(self, container_id: str) -> None:
        try:
            container = [c for c in self.containers if c.container_id == container_id][
                0
            ]
            shutil.rmtree(container.container_path)
            shutil.rmtree(container.data_input_path)
            shutil.rmtree(container.data_output_path)
            self.containers.remove(container)
        except IndexError:
            raise ValueError(f'no container with id "{container_id}"')

    def remove_all_containers(self) -> None:
        for container in self.containers:
            shutil.rmtree(container.container_path)
        self.containers = []

    def _init_pylot_code(self):
        if (not os.path.exists(PYLOT_MAIN_CLONE_DIR)) or (
            len(os.listdir(PYLOT_MAIN_CLONE_DIR)) == 0
        ):
            raise RuntimeError("Pylot submodule not initialized")

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if os.path.exists(os.path.join(PYLOT_MAIN_CLONE_DIR, "prf")):
            self.logger.info(f"Proffast 2.2 has already been downloaded")
        else:
            self.logger.info(f"Downloading Proffast 2.2 code")
            tum_esm_utils.shell.run_shell_command(
                command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
                working_directory=os.path.join(PYLOT_ROOT_DIR, "main"),
            )
            tum_esm_utils.shell.run_shell_command(
                command=f"unzip -q {ZIPFILE_NAME}",
                working_directory=os.path.join(PYLOT_ROOT_DIR, "main"),
            )
            os.remove(os.path.join(PYLOT_ROOT_DIR, "main", ZIPFILE_NAME))

        # COMPILE FORTRAN CODE
        self.logger.info(f"Compiling Fortran code of corrupt-ifgs detection")
        tum_esm_utils.shell.run_shell_command(
            command=f"bash compile.sh",
            working_directory=os.path.join(PROJECT_DIR, "src", "detect_corrupt_ifgs"),
        )
