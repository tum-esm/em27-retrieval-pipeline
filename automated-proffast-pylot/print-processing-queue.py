from src import utils


if __name__ == "__main__":
    config = utils.load_config()
    retrieval_queue = utils.RetrievalQueue(config)
    for session in retrieval_queue:
        print(session)
