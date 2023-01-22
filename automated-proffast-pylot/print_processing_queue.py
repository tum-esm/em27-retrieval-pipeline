from src import utils, interfaces


if __name__ == "__main__":
    config = utils.load_config()
    logger = utils.Logger("development")
    retrieval_queue = interfaces.RetrievalQueue(config, logger)
    while True:
        next_item = retrieval_queue.get_next_item()
        if next_item is None:
            break
        logger.info(f"next item: {next_item}")

    logger.info("done")
