import cProfile
from src import utils, interfaces


def run():
    config = utils.load_config()
    logger = utils.Logger("development", print_only=True)
    logger.info("starting")
    retrieval_queue = interfaces.RetrievalQueue(config, logger)
    while True:
        next_item = retrieval_queue.get_next_item()
        if next_item is None:
            break
        logger.info(f"next item: {next_item}")

    logger.info("no more items")


if __name__ == "__main__":
    run()  # cProfile.run("run()")
