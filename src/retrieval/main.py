import multiprocessing
import multiprocessing.context
import os
import signal
import sys
import time
from typing import Any

import em27_metadata
import tum_esm_utils

sys.path.append(tum_esm_utils.files.rel_to_abs_path("../.."))
from src import retrieval, types, utils


def run() -> None:
    main_logger = retrieval.utils.logger.Logger("main")
    main_logger.horizontal_line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")
    time.sleep(0.25)

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
        main_logger.info("Automation was stopped by user")
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

            container_factory.remove_container("-".join(process.name.split("-")[-2:]))
            main_logger.info(f'Process "{process.name}": removed container')

        main_logger.info("Killed all containers")
        retrieval.utils.retrieval_status.RetrievalStatusList.reset()
        main_logger.info("Reset retrieval status list")
        main_logger.info("Teardown is done")
        main_logger.archive()
        exit(0)

    signal.signal(signal.SIGINT, _graceful_teardown)
    signal.signal(signal.SIGTERM, _graceful_teardown)
    main_logger.info("Established graceful teardown hook")

    # load metadata interface
    try:
        em27_metadata_interface = utils.metadata.load_local_em27_metadata_interface()
        if em27_metadata_interface is not None:
            print("Found local metadata")
        else:
            print("Did not find local metadata -> fetching metadata from GitHub")
            assert config.general.metadata is not None, "Remote metadata not configured"
            em27_metadata_interface = em27_metadata.load_from_github(
                github_repository=config.general.metadata.github_repository,
                access_token=config.general.metadata.access_token,
            )
            print("Successfully fetched metadata from GitHub")
    except Exception as e:
        main_logger.exception(e, "Error while loading local metadata")
        main_logger.archive()
        raise e

    # generate retrieval queue
    retrieval.utils.retrieval_status.RetrievalStatusList.reset()
    job_queue = retrieval.utils.job_queue.RetrievalJobQueue()

    for job_index, job in enumerate(config.retrieval.jobs):
        main_logger.info(
            f"Generating retrieval queue for job {job_index+1}: {job.model_dump_json(indent=4)}"
        )
        retrieval_sdcs = retrieval.dispatching.retrieval_queue.generate_retrieval_queue(
            config, main_logger, em27_metadata_interface, job
        )
        main_logger.info(f"Found {len(retrieval_sdcs)} items for job {job_index+1}")
        for sdc in retrieval_sdcs:
            job_queue.push(
                job.retrieval_algorithm,
                job.atmospheric_profile_model,
                sdc,
                job.settings,
            )
        retrieval.utils.retrieval_status.RetrievalStatusList.add_items(
            retrieval_sdcs,
            retrieval_algorithm=job.retrieval_algorithm,
            atmospheric_profile_model=job.atmospheric_profile_model,
            output_suffix=job.settings.output_suffix,
        )
    main_logger.info(f"Generated retrieval queue with {len(job_queue)} items")
    main_logger.horizontal_line(variant="=")

    try:
        while True:
            # start as many new processes as possible
            while True:
                if len(processes) == config.retrieval.general.max_process_count:
                    break

                if job_queue.is_empty():
                    break

                # start new processes
                next_retrieval_job = job_queue.pop()
                assert next_retrieval_job is not None
                new_session = retrieval.session.create_session.run(
                    container_factory,
                    next_retrieval_job.sensor_data_context,
                    next_retrieval_job.retrieval_algorithm,
                    next_retrieval_job.atmospheric_profile_model,
                    next_retrieval_job.job_settings,
                )
                new_process = multiprocessing.get_context("spawn").Process(
                    target=retrieval.session.process_session.run,
                    args=(config, new_session),
                    name=(
                        f"retrieval-session-{new_session.ctx.sensor_id}-"
                        + f"{new_session.ctx.from_datetime.strftime('%Y-%m-%dT%H:%M:%S')}-"
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
                main_logger.info(f'process "{finished_process.name}": finished processing')
                container_factory.remove_container("-".join(finished_process.name.split("-")[-2:]))
                main_logger.info(f'process "{finished_process.name}": removed container')

            if job_queue.is_empty() and (len(processes) == 0):
                main_logger.info("No more things to process")
                break

            time.sleep(15)

    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt")
    except Exception as e:
        main_logger.exception(e, "Unexpected error")

    container_factory.remove_all_containers()
    main_logger.info("Automation is finished")
    main_logger.horizontal_line(variant="=")
    main_logger.archive()


if __name__ == "__main__":
    with utils.semaphores.with_automation_lock():
        run()
