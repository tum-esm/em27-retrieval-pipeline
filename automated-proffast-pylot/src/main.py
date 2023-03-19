import os
import time
from typing import Optional

import tum_esm_em27_metadata
from src import utils, interfaces, procedures
import multiprocessing
import multiprocessing.context

MAX_PARALLEL_PROCESSES = 9


def run() -> None:
    main_logger = utils.Logger("main")
    main_logger.horizontal_line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")

    # load config
    try:
        config = utils.load_config()
        main_logger.info("Config is valid")
    except:
        main_logger.error("Config file invalid")
        main_logger.exception()
        return

    # set up pylot dispatcher and session scheduler
    pylot_factory = interfaces.PylotFactory(main_logger)
    retrieval_queue = interfaces.RetrievalQueue(config, main_logger)
    processes: list[multiprocessing.context.SpawnProcess] = []

    main_logger.horizontal_line(variant="=")

    try:
        while True:

            # start as many new processes as possible
            next_sensor_data_context: Optional[
                tum_esm_em27_metadata.types.SensorDataContext
            ] = None
            while True:
                if len(processes) == MAX_PARALLEL_PROCESSES:
                    break

                next_sensor_data_context = retrieval_queue.get_next_item()
                if next_sensor_data_context is None:
                    break

                # start new processes
                new_session = procedures.create_session.run(
                    pylot_factory,
                    next_sensor_data_context,
                )
                new_process = multiprocessing.get_context("spawn").Process(
                    target=procedures.process_session.run,
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
    except Exception:
        main_logger.exception()

    pylot_factory.remove_all_containers()
    main_logger.info(f"Automation is finished")
    main_logger.horizontal_line(variant="=")
    main_logger.archive()
