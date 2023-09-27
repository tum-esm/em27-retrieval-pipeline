import signal
import sys
import filelock
import os
import time
from typing import Any, Optional
import tum_esm_em27_metadata
import multiprocessing
import multiprocessing.context
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(
    __file__, current_depth=2
)
sys.path.append(_PROJECT_DIR)

from src import custom_types, utils, interfaces, procedures

LOCK_FILE = f"{_PROJECT_DIR}/src/main.lock"
lock = filelock.FileLock(LOCK_FILE, timeout=0)


def run() -> None:
    main_logger = utils.proffast.Logger("main")
    main_logger.horizontal_line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")

    # load config
    try:
        config = custom_types.Config.load()
        main_logger.info("Config is valid")
    except Exception as e:
        main_logger.exception(e, "Config file invalid")
        return

    if config.proffast is None:
        main_logger.error("Proffast not configured in config file")
        exit(1)

    # set up process list and container factory
    container_factory = interfaces.proffast.ContainerFactory(
        config, main_logger
    )
    processes: list[multiprocessing.context.SpawnProcess] = []

    # tear down logger gracefully when process is killed

    def _graceful_teardown(*args: Any) -> None:
        main_logger.info(f"Automation was stopped by user")
        main_logger.info(f"Killing {len(processes)} container(s)")
        for process in processes:
            process.terminate()
            kill_time = time.time()
            while True:
                if not process.is_alive():
                    main_logger.info(f'Process "{process.name}": stopped')
                    break
                if time.time() - kill_time > 5:
                    main_logger.warning(
                        f'Process "{process.name}": did not terminate after 5 seconds, sending SIGKILL'
                    )
                    process.kill()
                if time.time() - kill_time > 10:
                    main_logger.warning(
                        f'Process "{process.name}": could not get killed 10 seconds'
                    )
                    break

                time.sleep(0.2)

            container_factory.remove_container(process.name.split("-")[-1])
            main_logger.info(f'Process "{process.name}": removed container')

        main_logger.info(f"Teardown is done")
        main_logger.archive()
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    main_logger.info("Established graceful teardown hook")

    # set up pylot dispatcher and session scheduler
    retrieval_queue = interfaces.proffast.RetrievalQueue(config, main_logger)
    main_logger.horizontal_line(variant="=")

    try:
        while True:
            # start as many new processes as possible
            next_sensor_data_context: Optional[
                tum_esm_em27_metadata.types.SensorDataContext] = None
            while True:
                if len(processes) == config.proffast.general.max_core_count:
                    break

                next_sensor_data_context = retrieval_queue.get_next_item()
                if next_sensor_data_context is None:
                    break

                # start new processes
                new_session = procedures.proffast.create_session.run(
                    container_factory,
                    next_sensor_data_context,
                )
                new_process = multiprocessing.get_context("spawn").Process(
                    target=procedures.proffast.process_session.run,
                    args=(config, new_session),
                    name=(
                        f"pylot-session-{new_session.ctx.sensor_id}-" +
                        f"{new_session.ctx.from_datetime.strftime('%Y-%m-%dT%H:%M:%S')}-"
                        + f"{new_session.ctn.container_id}"
                    ),
                    daemon=True,
                )
                processes.append(new_process)
                main_logger.info(f'process "{new_process.name}": starting')
                new_process.start()

            # stop as many finished processes as possible
            for finished_process in [p for p in processes if not p.is_alive()]:
                finished_process.join()
                processes.remove(finished_process)
                main_logger.info(
                    f'process "{finished_process.name}": finished processing'
                )
                container_factory.remove_container(
                    finished_process.name.split("-")[-1]
                )
                main_logger.info(
                    f'process "{finished_process.name}": removed container'
                )

            if (next_sensor_data_context is None) and (len(processes) == 0):
                main_logger.info(f"No more things to process")
                break

            time.sleep(15)

    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt")
    except Exception as e:
        main_logger.exception(e, "Unexpected error")

    container_factory.remove_all_containers()
    main_logger.info(f"Automation is finished")
    main_logger.horizontal_line(variant="=")
    main_logger.archive()


if __name__ == "__main__":
    try:
        lock.acquire()
        try:
            run()
        finally:
            lock.release()
    except filelock.Timeout:
        print("process is already running")
