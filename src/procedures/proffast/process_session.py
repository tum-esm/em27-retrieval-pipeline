from src import custom_types, interfaces, utils
import signal
from . import (
    move_log_files,
    move_profiles,
    move_ifg_files,
    run_proffast_pylot,
    move_outputs,
)


def run(config: custom_types.Config, pylot_session: custom_types.PylotSession) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logger = utils.proffast.Logger(container_id=pylot_session.ctn.container_id)
    logger.info(
        f"Starting session {pylot_session.ctx.sensor_id}/"
        + f"{pylot_session.ctx.from_datetime}-{pylot_session.ctx.to_datetime}"
    )

    def log_input_warning(message: str) -> None:
        interfaces.proffast.InputWarningsInterface.add(
            pylot_session.ctx.sensor_id, pylot_session.ctx.from_datetime, message
        )
        logger.warning(message)
        logger.archive()

    try:
        move_profiles.run(config, pylot_session)
    except Exception as e:
        log_input_warning(f"Inputs incomplete (vertical profiles): {e}")
        return

    try:
        move_log_files.run(config, logger, pylot_session)
    except Exception as e:
        log_input_warning(f"Inputs incomplete (datalogger files): {e}")
        return

    try:
        move_ifg_files.run(config, logger, pylot_session)
    except Exception as e:
        log_input_warning(f"Inputs incomplete (ifg files): {e}")
        return

    # inputs complete no warning to consider anymore
    interfaces.proffast.InputWarningsInterface.remove(
        pylot_session.ctx.sensor_id,
        pylot_session.ctx.from_datetime,
    )

    logger.info(f"Running the pylot")
    try:
        run_proffast_pylot.run(pylot_session)
        logger.debug("Pylot execution was successful")
    except Exception as e:
        logger.exception(e, label="Pylot execution failed")

    # uncomment the following return if you want to observe the final
    # proffast outputs of one day in this working directory
    # return

    logger.info(f"Moving the outputs")
    try:
        move_outputs.run(config, logger, pylot_session)
        logger.info(f"Finished")
    except AssertionError as e:
        logger.exception(e, label="Moving outputs failed")

    logger.archive()
