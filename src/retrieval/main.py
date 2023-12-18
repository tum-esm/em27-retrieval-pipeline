import queue
from typing import Any, Optional
import signal
import sys
import os
import time
import em27_metadata
import multiprocessing
import multiprocessing.context
import tum_esm_utils

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import types, utils, retrieval


def run() -> None:
    main_logger = retrieval.utils.logger.Logger("main")
    main_logger.horizontal_line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")

    # load config
    try:
        config = types.Config.load()
        main_logger.info("Config is valid")
    except Exception as e:
        main_logger.exception(e, "Config file invalid")
        return

    assert config.retrieval is not None, "no retrieval config found"

    # set up process list and container factory
    container_factory = retrieval.dispatching.container_factory.ContainerFactory(
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

        main_logger.info(f"Killed all containers")
        retrieval.utils.retrieval_status.RetrievalStatusList.reset()
        main_logger.info(f"Reset retrieval status list")
        main_logger.info(f"Teardown is done")
        main_logger.archive()
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    main_logger.info("Established graceful teardown hook")

    # load metadata interface
    em27_metadata_interface = em27_metadata.load_from_github(
        github_repository=config.general.metadata.github_repository,
        access_token=config.general.metadata.access_token,
    )
    main_logger.info(f"Loaded metadata from github")

    # generate retrieval queue
    retrieval.utils.retrieval_status.RetrievalStatusList.reset()
    retrieval_queue: queue.Queue[tuple[types.RetrievalAlgorithm,
                                       types.AtmosphericProfileModel,
                                       em27_metadata.types.SensorDataContext]
                                ] = queue.Queue()
    for job_index, job in enumerate(config.retrieval.jobs):
        main_logger.info(
            f"Generating retrieval queue for job {job_index+1}: {job.model_dump_json()}"
        )
        job_retrieval_queue = retrieval.dispatching.retrieval_queue.generate_retrieval_queue(
            config, main_logger, em27_metadata_interface, job
        )
        main_logger.info(
            f"Found {len(job_retrieval_queue)} items for job {job_index+1}"
        )
        for item in job_retrieval_queue:
            retrieval_queue.put(
                (job.retrieval_algorithm, job.atmospheric_profile_model, item)
            )
        retrieval.utils.retrieval_status.RetrievalStatusList.add_items(
            job_retrieval_queue,
            retrieval_algorithm=job.retrieval_algorithm,
            atmospheric_profile_model=job.atmospheric_profile_model
        )
    main_logger.info(
        f"Generated retrieval queue with {retrieval_queue.qsize()} items"
    )
    main_logger.horizontal_line(variant="=")

    try:
        while True:
            next_sensor_data_context: Optional[
                tuple[types.RetrievalAlgorithm, types.AtmosphericProfileModel,
                      em27_metadata.types.SensorDataContext]] = None

            # start as many new processes as possible
            while True:
                if len(processes) == config.retrieval.general.max_process_count:
                    break

                try:
                    next_sensor_data_context = retrieval_queue.get()
                except queue.Empty:
                    break

                # start new processes
                new_session = retrieval.session.create_session.run(
                    container_factory,
                    next_sensor_data_context[2],
                    next_sensor_data_context[0],
                    next_sensor_data_context[1],
                )
                new_process = multiprocessing.get_context("spawn").Process(
                    target=retrieval.session.process_session.run,
                    args=(config, new_session),
                    name=(
                        f"retrieval-session-{new_session.ctx.sensor_id}-" +
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
                    "-".join(finished_process.name.split("-")[-2 :])
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
    with utils.semaphores.with_automation_lock():
        run()
