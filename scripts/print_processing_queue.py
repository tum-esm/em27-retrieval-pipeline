import sys
import tum_esm_utils

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=2)
sys.path.append(PROJECT_DIR)

from src import utils, interfaces


if __name__ == "__main__":
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
