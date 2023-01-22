import json
import os
from typing import List
from src import utils, interfaces, procedures
import multiprocessing
import multiprocessing.pool


def run() -> None:
    main_logger = utils.Logger("main")
    pylot_factory = interfaces.PylotFactory(main_logger)
    pool = multiprocessing.Pool(4)

    main_logger.line(variant="=")
    main_logger.info(f"Starting the automation with PID {os.getpid()}")

    try:
        config = utils.load_config(validate=True)
    except:
        main_logger.error("Config file invalid")
        main_logger.exception()
        return

    try:
        retrieval_queue = interfaces.RetrievalQueue(config, main_logger, pylot_factory)
        results: List[multiprocessing.pool.AsyncResult] = []

        for sensor_data_context in retrieval_queue:
            session = procedures.create_session.run(pylot_factory, sensor_data_context)
            main_logger.info(f"Running session: {json.dumps(session.dict(), indent=4)}")

            results.append(
                pool.apply_async(
                    func=procedures.process_session,
                    args=(config, session, pylot_factory),
                )
            )
        [result.get() for result in results]

    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt")
        pylot_factory.clean_up()
        pool.terminate()
        return
    except Exception:
        main_logger.exception()
        pylot_factory.clean_up()
        pool.terminate()
        return

    pylot_factory.clean_up()
    main_logger.info(f"Automation is finished")
