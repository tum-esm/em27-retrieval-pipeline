from typing import Literal
import os
import shutil
import tum_esm_utils
from src import retrieval
from src import types, utils

_RETRIEVAL_CODE_DIR = os.path.join("../algorithms/")


class ContainerFactory:
    """Factory for creating pylot containers.

    The pylot containers are created by copying the pylot code from the
    main directory and compiling the fortran code. Each container will
    have a unique id and is initialized with empty input and output
    directories.

    The factory keeps track of all containers and can remove them."""
    def __init__(
        self,
        config: types.Config,
        logger: retrieval.utils.logger.Logger,
    ):
        """Initialize the factory.

        The `__init__` function will download the Proffast 2.2 code
        from the KIT website."""

        self.config = config
        self.logger = logger
        self.containers: list[types.ProffastContainer] = []

        assert self.config.retrieval is not None
        retrieval_algorithms = [
            job.algorithm for job in self.config.retrieval.jobs
        ]
        if "proffast-1.0" in retrieval_algorithms:
            self.logger.info("Initializing for Proffast 1.0")
            self._init_proffast10_code()
        if "proffast-2.2" in retrieval_algorithms:
            self.logger.info("Initializing ContainerFactory for Proffast 2.2")
            self._init_proffast22_code()
        if "proffast-2.3" in retrieval_algorithms:
            self.logger.info("Initializing ContainerFactory for Proffast 2.3")
            self._init_proffast23_code()

        self.logger.info("ContainerFactory is set up")

    def create_container(
        self,
        retrieval_algorithm: types.RetrievalAlgorithm,
    ) -> types.RetrievalContainer:
        """Create a new container and return it.

        The container is created by copying the pylot code from the main
        directory and compiling the fortran code. The container is then
        initialized with empty input and output directories."""

        new_container_id = utils.text.get_random_container_name(
            currently_used_names=[c.container_id for c in self.containers]
        )
        container: types.RetrievalContainer

        assert self.config.retrieval is not None
        if retrieval_algorithm == "proffast-1.0":
            container = types.Proffast10Container(container_id=new_container_id)
        if retrieval_algorithm == "proffast-2.2":
            container = types.Proffast22Container(container_id=new_container_id)
        if retrieval_algorithm == "proffast-2.3":
            container = types.Proffast23Container(container_id=new_container_id)

        # copy and install the retrieval code into the container
        retrieval_code_root_dir = os.path.join(
            _RETRIEVAL_CODE_DIR, retrieval_algorithm
        )
        shutil.copytree(
            os.path.join(retrieval_code_root_dir, "main"),
            container.container_path,
        )
        installer_script_path = os.path.join(
            retrieval_code_root_dir, "install.sh"
        )
        if os.path.isfile(installer_script_path):
            tum_esm_utils.shell.run_shell_command(
                command=installer_script_path,
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
            container = [
                c for c in self.containers if c.container_id == container_id
            ][0]
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
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-1.0", "main")

        # DOWNLOAD PROFFAST 1.0 code if it doesn't exist yet
        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            self.logger.info(f"Proffast 1.0 has already been downloaded")
            return

        self.logger.info(f"Downloading Proffast 1.0 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        os.rename(
            os.path.join(ROOT_DIR, "2021-03-08_prf96-EM27-fast"),
            os.path.join(ROOT_DIR, "prf"),
        )

        # clean up unused directories
        for d in [
            os.path.join(ROOT_DIR, "prf", "preprocess", "125HR-garmisch"),
            os.path.join(ROOT_DIR, "prf", "preprocess", "125HR-karlsruhe"),
            os.path.join(ROOT_DIR, "prf", "preprocess", "sod2017_em27sn039"),
            os.path.join(ROOT_DIR, "prf", "out_fast", "sod2017_em27sn039"),
            os.path.join(
                ROOT_DIR, "prf", "out_fast", "sod2017_em27sn039_Linux"
            ),
            os.path.join(ROOT_DIR, "prf", "analysis"),
            os.path.join(ROOT_DIR, "prf", "source"),
        ]:
            shutil.rmtree(d)

        # clean up unused files
        for f in [
            os.path.join(ROOT_DIR, ZIPFILE_NAME),
            os.path.join(ROOT_DIR, "prf", "continue.txt"),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "invers10_sod2017_em27sn039_170608.inp"
            ),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "invers10_sod2017_em27sn039_170609.inp"
            ),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "pcxs10_sod2017_em27sn039_170608.inp"
            ),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "pcxs10_sod2017_em27sn039_170609.inp"
            ),
        ]:
            os.remove(f)

        # remove other unused files
        os.system("rm " + os.path.join(ROOT_DIR, "prf", "*.py"))
        os.system("rm " + os.path.join(ROOT_DIR, "prf", "invers10*"))
        os.system("rm " + os.path.join(ROOT_DIR, "prf", "pcxs10*"))

    def _init_proffast22_code(self) -> None:
        """Initialize the Proffast 2.2 and pylot 1.1 code.

        It will download the Proffast 2.2 code from the KIT website
        (https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.2.zip)
        and copy it to the directory `src/prfpylot/main/prf`."""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "PROFFASTv2.2.zip"
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-2.2", "main")

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            self.logger.info(f"Proffast 2.2 has already been downloaded")
            return

        self.logger.info(f"Downloading Proffast 2.2 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        os.remove(os.path.join(ROOT_DIR, ZIPFILE_NAME))

    def _init_proffast23_code(self) -> None:
        """Initialize the Proffast 2.3 and pylot 1.2 code.

        It will download the Proffast 2.3 code from the KIT website
        (https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.3.zip)
        and copy it to the directory `src/prfpylot/main/prf`."""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "PROFFASTv2.3.zip"
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-2.3", "main")

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            self.logger.info(f"Proffast 2.3 has already been downloaded")
            return

        self.logger.info(f"Downloading Proffast 2.3 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        os.remove(os.path.join(ROOT_DIR, ZIPFILE_NAME))
