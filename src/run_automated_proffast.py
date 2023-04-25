import sys
import filelock
import os
import time
from typing import Optional
import tum_esm_em27_metadata
import multiprocessing
import multiprocessing.context
import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
sys.path.append(_PROJECT_DIR)

from src import utils, interfaces, procedures

LOCK_FILE = f"{_PROJECT_DIR}/src/main.lock"
lock = filelock.FileLock(LOCK_FILE, timeout=0)


def run() -> None:
    main_logger = utils.automated_proffast.Logger("main")
    main_logger.horizontal_line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")

    # load config
    try:
        config = utils.load_config()
        main_logger.info("Config is valid")
    except Exception as e:
        main_logger.exception(e, "Config file invalid")
        return

    # set up pylot dispatcher and session scheduler
    pylot_factory = interfaces.automated_proffast.PylotFactory(main_logger)
    retrieval_queue = interfaces.automated_proffast.RetrievalQueue(config, main_logger)
    processes: list[multiprocessing.context.SpawnProcess] = []

    main_logger.horizontal_line(variant="=")

    try:
        while True:
            # start as many new processes as possible
            next_sensor_data_context: Optional[
                tum_esm_em27_metadata.types.SensorDataContext
            ] = None
            while True:
                if len(processes) == config.automated_proffast.max_core_count:
                    break

                next_sensor_data_context = retrieval_queue.get_next_item()
                if next_sensor_data_context is None:
                    break

                # start new processes
                new_session = procedures.automated_proffast.create_session.run(
                    pylot_factory,
                    next_sensor_data_context,
                )
                new_process = multiprocessing.get_context("spawn").Process(
                    target=procedures.automated_proffast.process_session.run,
                    args=(config, new_session),
                    name=(
                        f"pylot-session-{new_session.sensor_id}-"
                        + f"{new_session.date}-{new_session.container_id}"
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
                pylot_factory.remove_container(finished_process.name.split("-")[-1])
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

    pylot_factory.remove_all_containers()
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
