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
    container_id = ""

    def __init__(self, container_id: str) -> None:
        self.container_id = container_id

    def _print(self, m: str, level: str) -> None:
        t = datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
        log_line = f"{t} - {level} - {m}\n"
        with open(f"{PROJECT_DIR}/logs/{self.container_id}_{log_file_name}", "a") as f:
            f.write(log_line)
            Logger._session_logs.append(log_line)

    def exception(self) -> None:
        """log an exception and its traceback"""
        exc_type, exc_value, exc_traceback = sys.exc_info()
        assert exc_type is not None, "no exeception is present"
        name = f"Unhandeled Exception: {exc_type.__name__}\n"
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self._print(name + tb, "EXCEPTION")

    def error(self, m: str) -> None:
        self._print(m, "ERROR")

    def warning(self, m: str) -> None:
        self._print(m, "WARNING")

    def info(self, m: str) -> None:
        self._print(m, "INFO")

    def debug(self, m: str) -> None:
        self._print(m, "DEBUG")

    def line(self, variant: str = "-") -> None:
        """log a vertical line with 52 characters"""
        self._print(variant * 52, "INFO")

    def flush_session_logs(self) -> None:
        """
        Reset the current session-logs (= log lines from
        one sensor-date-combination)
        """
        self._session_logs = []

    def get_session_logs() -> list[str]:
        """
        Return the current session-logs (= log lines from
        one sensor-date-combination)
        """
        return Logger._session_logs
