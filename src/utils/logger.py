from datetime import datetime
import os
import sys
import traceback

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))
LOG_FILEPATH = f"{PROJECT_DIR}/logs/automation.log"

# I am not using the logging-library because the proffast-pylot
# also uses that and figuring out how to not make these two
# interfere is not worth it

# the logfile name will have the time when the script has been started
log_file_name = datetime.utcnow().strftime("%Y%m%d-%H-%M.log")


class Logger:
    _session_logs: list[str] = []

    @staticmethod
    def _print(m: str, level: str) -> None:
        t = datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
        with open(f"{PROJECT_DIR}/logs/{log_file_name}", "a") as f:
            log_line = f"{t} - {level} - {m}\n"
            f.write(log_line)
            Logger._session_logs.append(log_line)

    @staticmethod
    def exception() -> None:
        """log an exception and its traceback"""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        name = f"Unhandeled Exception: {exc_type.__name__}\n"
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        Logger._print(name + tb, "EXCEPTION")

    @staticmethod
    def error(m: str) -> None:
        Logger._print(m, "ERROR")

    @staticmethod
    def warning(m: str) -> None:
        Logger._print(m, "WARNING")

    @staticmethod
    def info(m: str) -> None:
        Logger._print(m, "INFO")

    @staticmethod
    def debug(m: str) -> None:
        Logger._print(m, "DEBUG")

    @staticmethod
    def line(variant: str = "-") -> None:
        """log a vertical line with 52 characters"""
        Logger._print(variant * 52, "INFO")

    @staticmethod
    def flush_session_logs() -> None:
        """
        Reset the current session-logs (= log lines from
        one sensor-date-combination)
        """
        Logger._session_logs = []

    @staticmethod
    def get_session_logs() -> list[str]:
        """
        Return the current session-logs (= log lines from
        one sensor-date-combination)
        """
        return Logger._session_logs
