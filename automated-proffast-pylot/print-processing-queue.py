from src import utils, interfaces


if __name__ == "__main__":
    config = utils.load_config()
    retrieval_queue = interfaces.RetrievalQueue(config)
    while True:
        next_item = retrieval_queue.get_next_item()
        if next_item is None:
            break
        print(next_item)
