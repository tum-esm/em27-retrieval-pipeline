from datetime import datetime
import os
import shutil
import sys
import traceback

dir = os.path.dirname
PROJECT_DIR = dir(dir(dir(os.path.abspath(__file__))))

# I am not using the logging-library because the proffast-pylot
# also uses that and figuring out how to not make these two
# interfere is not worth it

# the logfile name will have the time when the script has been started
logfile_time = datetime.utcnow().strftime("%Y%m%d-%H-%M")


class Logger:
    def __init__(self, container_id: str, print_only: bool = False) -> None:
        self.container_id = container_id
        self.logfile_name = f"{logfile_time}_{self.container_id}.log"
        self.logfile_path = os.path.join(PROJECT_DIR, "logs", self.logfile_name)
        self.print_only = print_only

    def _print(self, m: str, level: str) -> None:
        t = datetime.utcnow().strftime("%Y%m%d %H:%M:%S")
        log_line = f"{t} - {level} - {m}\n"
        if self.print_only:
            print(log_line, end="")
        else:
            with open(self.logfile_path, "a") as f:
                f.write(log_line)

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

    def horizontal_line(self, variant: str = "-") -> None:
        """
        log a horizontal line with 52 characters
        why 52? that is a very good question!
        """
        self._print(variant * 52, "INFO")

    def archive(self) -> None:
        """move the used log file into the archive"""
        shutil.copyfile(
            self.logfile_path,
            os.path.join(PROJECT_DIR, "logs", "archive", self.logfile_name),
        )
