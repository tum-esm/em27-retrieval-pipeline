from datetime import datetime
import os

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
LOG_FILEPATH = f"{PROJECT_DIR}/logs/automation.log"

# I am not using the logging-library because the proffast-pylot
# also uses that and figuring out how to not make these two
# interfere is not worth it


class Logger:
    @staticmethod
    def _print(m: str, level: str):
        t = datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
        log_file_name = datetime.utcnow().strftime("%Y%m%d-automation.log")
        with open(f"{PROJECT_DIR}/logs/automation/{log_file_name}", "a") as f:
            f.write(f"{t} - {level} - {m}\n")

    @staticmethod
    def exception(m: str):
        # TODO: Log traceback (see pyra-4 emails)
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
