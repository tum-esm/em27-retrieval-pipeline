import glob
import os
import shutil
from src import custom_types, utils
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_PYLOT_ROOT_DIR = os.path.join(_PROJECT_DIR, "src", "pylot_src")
_PYLOT_MAIN_CLONE_DIR = os.path.join(_PYLOT_ROOT_DIR, "main")
_CONTAINERS_DIR = os.path.join(_PROJECT_DIR, "data", "containers")

_KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
_ZIPFILE_NAME = "PROFFASTv2.2.zip"


class PylotFactory:
    """Factory for creating pylot containers.

    The pylot containers are created by copying the pylot code from the
    main directory and compiling the fortran code. Each container will
    have a unique id and is initialized with empty input and output
    directories.

    The factory keeps track of all containers and can remove them."""

    def __init__(self, logger: utils.automated_proffast.Logger):
        """Initialize the factory.

        The `__init__` function will download the Proffast 2.2 code
        from the KIT website."""

        self.logger = logger
        self.containers: list[custom_types.PylotContainer] = []
        self._init_pylot_code()
        self.logger.info("PylotFactory is set up")

    def create_container(self) -> custom_types.PylotContainer:
        """Create a new container and return it.

        The container is created by copying the pylot code from the main
        directory and compiling the fortran code. The container is then
        initialized with empty input and output directories.

        Return example:

        ```python
        hub = ".../automated-proffast-pylot/src/prfpylot/containers"
        new_id = "pylot-container-1234567890"

        PylotContainer(
            container_id=new_id,
            container_path=f"{hub}/{new_id}",
            data_input_path=f"{hub}/{new_id}-input",
            data_output_path=f"{hub}/{new_id}-output",
            pylot_config_path=f"{hub}/{new_id}/pylot_config.yml",
            pylot_log_format_path=f"{hub}/{new_id}/pylot_log_format.yml",
        )
        """
        container_id = tum_esm_utils.text.get_random_string(
            length=10, forbidden=[c.container_id for c in self.containers]
        )

        # copy container code and compile the fortran code
        container_path = os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{container_id}",
        )
        shutil.copytree(_PYLOT_MAIN_CLONE_DIR, container_path)
        tum_esm_utils.shell.run_shell_command(
            command=f"{os.path.join(_PYLOT_ROOT_DIR, 'install_proffast_linux.sh')}",
            working_directory=os.path.join(container_path, "prf"),
        )

        # generate empty input directory
        data_input_path = os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{container_id}-inputs",
        )
        os.mkdir(data_input_path)
        os.mkdir(os.path.join(data_input_path, "ifg"))
        os.mkdir(os.path.join(data_input_path, "map"))
        os.mkdir(os.path.join(data_input_path, "log"))

        # generate empty output directory
        data_output_path = os.path.join(
            _CONTAINERS_DIR,
            f"pylot-container-{container_id}-outputs",
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
        """Remove a container by its id.

        It will remove the pylot code, the input and output directories
        of the container. It raises an IndexError if no container with
        the given id exists.
        """
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
        """Remove all containers."""
        for container in self.containers:
            shutil.rmtree(container.container_path)
        self.containers = []

    def _init_pylot_code(self) -> None:
        """Initialize the pylot code.

        It will download the Proffast 2.2 code from the KIT website
        (https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.2.zip)
        and copy it to the directory `src/prfpylot/main/prf`."""

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if os.path.exists(os.path.join(_PYLOT_MAIN_CLONE_DIR, "prf")):
            self.logger.info(f"Proffast 2.2 has already been downloaded")
        else:
            self.logger.info(f"Downloading Proffast 2.2 code")
            tum_esm_utils.shell.run_shell_command(
                command=f"wget --quiet {_KIT_BASE_URL}/{_ZIPFILE_NAME}",
                working_directory=os.path.join(_PYLOT_ROOT_DIR, "main"),
            )
            tum_esm_utils.shell.run_shell_command(
                command=f"unzip -q {_ZIPFILE_NAME}",
                working_directory=os.path.join(_PYLOT_ROOT_DIR, "main"),
            )
            os.remove(os.path.join(_PYLOT_ROOT_DIR, "main", _ZIPFILE_NAME))

            # fix fortran code
            for fortran_file_path in glob.glob(
                f"{_PYLOT_ROOT_DIR}/main/prf/source/*/*.f90"
            ):
                file_content = tum_esm_utils.files.load_file(fortran_file_path)
                for replacement in [
                    (
                        'character(len=1),parameter :: pathstr = "\\"',
                        'character(len=1),parameter::pathstr="/"',
                    ),
                    (
                        "character(150)",
                        "character(300)",
                    ),
                ]:
                    file_content = file_content.replace(*replacement)
                tum_esm_utils.files.dump_file(fortran_file_path, file_content)
