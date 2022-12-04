from . import utils


def run() -> None:
    config = utils.load_config()
    print(config)
