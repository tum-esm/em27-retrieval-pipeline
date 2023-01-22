import os
import shutil
from src import custom_types, utils


dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))

PYLOT_ROOT_DIR = os.path.join(PROJECT_DIR, "src", "prfpylot")
KIT_BASE_URL = "wget https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
ZIPFILE_NAME = "PROFFASTv2.2.zip"

EXECUTABLE_FILEPATHS = [
    os.path.join(PYLOT_ROOT_DIR, "main", "prf", "preprocess", "preprocess4"),
    os.path.join(PYLOT_ROOT_DIR, "main", "prf", "pcxs20"),
    os.path.join(PYLOT_ROOT_DIR, "main", "prf", "invers20"),
    os.path.join(PROJECT_DIR, "src", "detect_corrupt_ifgs", "parser", "ifg_parser"),
]


class PylotFactory:
    def __init__(self, logger: utils.Logger):
        self.logger = logger
        self.containers: list[custom_types.PylotContainer] = []
        self._init_pylot_code()

        print(f"prfpylot of main copy successful")

    def create_container(self) -> custom_types.PylotContainer:
        container_id = utils.get_random_string(
            length=10, forbidden=[c.container_id for c in self.containers]
        )

        # copy container code
        container_path = os.path.join(
            PYLOT_ROOT_DIR,
            f"pylot-container-{container_id}",
        )
        shutil.copytree(os.path.join(PYLOT_ROOT_DIR, "main"), container_path)

        # generate empty input directory
        data_input_path = os.path.join(
            PYLOT_ROOT_DIR,
            f"pylot-container-{container_id}-input",
        )
        os.mkdir(data_input_path)
        os.mkdir(os.path.join(data_input_path, "ifg"))
        os.mkdir(os.path.join(data_input_path, "map"))
        os.mkdir(os.path.join(data_input_path, "log"))

        # generate empty output directory
        data_output_path = os.path.join(
            PYLOT_ROOT_DIR,
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
            self.containers.remove(container)
        except IndexError:
            raise ValueError(f'no container with id "{container_id}"')

    def remove_all_containers(self) -> None:
        for container in self.containers:
            shutil.rmtree(container.container_path)
        self.containers = []

    def _init_pylot_code(self):
        if (not os.path.exists(self.main)) or (len(os.listdir(self.main)) == 0):
            raise RuntimeError("Pylot submodule not initialized")

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if not os.path.exists(os.path.join(self.main, "prf")):
            self.logger.info(f"downloading proffast code")

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
            if not os.path.isfile(filepath):
                raise FileNotFoundError(
                    f'file "{filepath}" does not exist after compilation'
                )

        self.logger.info(f"fortran compilation is done")
