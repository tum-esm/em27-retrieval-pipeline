import os
import shutil
from src import custom_types, utils
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_RETRIEVAL_CODE_DIR = os.path.join(_PROJECT_DIR, "src", "retrieval")


class ContainerFactory:
    """Factory for creating pylot containers.

    The pylot containers are created by copying the pylot code from the
    main directory and compiling the fortran code. Each container will
    have a unique id and is initialized with empty input and output
    directories.

    The factory keeps track of all containers and can remove them."""

    def __init__(self, config: custom_types.Config, logger: utils.proffast.Logger):
        """Initialize the factory.

        The `__init__` function will download the Proffast 2.2 code
        from the KIT website."""

        self.config = config
        self.logger = logger
        self.containers: list[
            custom_types.Proffast10Container | custom_types.Proffast22Container
        ] = []

        assert self.config.automated_proffast is not None
        if self.config.automated_proffast.general.retrieval_software == "proffast-1.0":
            self.logger.info("Initializing ContainerFactory for Proffast 1.0")
            self._init_proffast10_code()
        else:
            self.logger.info("Initializing ContainerFactory for Proffast 2.2")
            self._init_proffast22_code()

        self.logger.info("ContainerFactory is set up")

    def create_container(
        self,
    ) -> custom_types.Proffast10Container | custom_types.Proffast22Container:
        """Create a new container and return it.

        The container is created by copying the pylot code from the main
        directory and compiling the fortran code. The container is then
        initialized with empty input and output directories."""

        new_container_id = tum_esm_utils.text.get_random_string(
            length=10, forbidden=[c.container_id for c in self.containers]
        )
        container: custom_types.Proffast10Container | custom_types.Proffast22Container

        assert self.config.automated_proffast is not None
        if self.config.automated_proffast.general.retrieval_software == "proffast-1.0":
            container = custom_types.Proffast10Container(container_id=new_container_id)
        else:
            container = custom_types.Proffast22Container(container_id=new_container_id)

        # copy and install the retrieval code into the container
        retrieval_code_root_dir = os.path.join(
            _RETRIEVAL_CODE_DIR,
            self.config.automated_proffast.general.retrieval_software,
        )
        shutil.copytree(
            os.path.join(retrieval_code_root_dir, "main"),
            container.container_path,
        )
        tum_esm_utils.shell.run_shell_command(
            command=os.path.join(retrieval_code_root_dir, "install.sh"),
            working_directory=container.container_path,
        )

        # generate empty input directory
        os.mkdir(container.data_input_path)
        os.mkdir(os.path.join(container.data_input_path, "ifg"))
        os.mkdir(os.path.join(container.data_input_path, "map"))
        os.mkdir(os.path.join(container.data_input_path, "log"))

        # generate empty output directory
        os.mkdir(container.data_output_path)

        # bundle container paths together
        self.containers.append(container)

        return container

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

    def _init_proffast10_code(self) -> None:
        """Initialize the Proffast 1.0 code"""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "2021-03-08_prf96-EM27-fast.zip"

        root_dir = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-1.0")

        # DOWNLOAD PROFFAST 1.0 code if it doesn't exist yet
        if os.path.exists(os.path.join(root_dir, "main", "prf")):
            self.logger.info(f"Proffast 1.0 has already been downloaded")
            return

        self.logger.info(f"Downloading Proffast 1.0 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=os.path.join(root_dir, "main"),
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=os.path.join(root_dir, "main"),
        )
        os.rename(
            os.path.join(root_dir, "main", "2021-03-08_prf96-EM27-fast"),
            os.path.join(root_dir, "main", "prf"),
        )
        os.remove(os.path.join(root_dir, "main", ZIPFILE_NAME))

    def _init_proffast22_code(self) -> None:
        """Initialize the Proffast 2.2 and pylot 1.1 code.

        It will download the Proffast 2.2 code from the KIT website
        (https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.2.zip)
        and copy it to the directory `src/prfpylot/main/prf`."""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "PROFFASTv2.2.zip"

        root_dir = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-2.2")

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if os.path.exists(os.path.join(root_dir, "main", "prf")):
            self.logger.info(f"Proffast 2.2 has already been downloaded")
            return

        self.logger.info(f"Downloading Proffast 2.2 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=os.path.join(root_dir, "main"),
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=os.path.join(root_dir, "main"),
        )
        os.remove(os.path.join(root_dir, "main", ZIPFILE_NAME))
