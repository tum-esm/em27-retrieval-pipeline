import os
from src import custom_types, utils

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


def run(
    session: custom_types.Session,
    pylot_factory: custom_types.PylotFactory,
    logger: utils.Logger,
) -> None:
    yaml_path = (
        f"{PROJECT_DIR}/inputs/{session.container_id}/"
        + f"{session.sensor_id}-pylot-config.yml"
    )
    result = pylot_factory.execute_pylot(session.container_id, yaml_path, 1)
    logger.info(f"Pylot instance result {result.returncode}")
    logger.info(f"Pylot Execution Logs: {result.stdout}")
    logger.error(f"Pylot Execution Logs: {result.stderr}")
