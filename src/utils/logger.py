from datetime import datetime
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
LOG_FILEPATH = f"{PROJECT_DIR}/logs/automation.log"

# TODO: Use logging module, Problem: The pylot also logs stuff


class Logger:
    @staticmethod
    def _print(m: str, level: str):
        t = datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
        with open(LOG_FILEPATH, "a") as f:
            f.write(f"{t} - {level} - {m}\n")

    @staticmethod
    def exception(m: str):
        Logger._print(m, "EXCEPTION")

    @staticmethod
    def error(m: str):
        Logger._print(m, "ERROR")

    @staticmethod
    def warning(m: str):
        Logger._print(m, "WARNING")

    @staticmethod
    def info(m: str):
        Logger._print(m, "INFO")

    @staticmethod
    def debug(m: str):
        Logger._print(m, "DEBUG")
