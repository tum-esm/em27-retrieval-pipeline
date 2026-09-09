import datetime
import os
import shutil
import traceback
from typing import Literal, Optional

import tum_esm_utils

_PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=4)
_DEFAULT_LOGS_DIR = os.path.join(_PROJECT_DIR, "data", "logs")


def _get_retrieval_logs_dir() -> str:
    logs_dir = os.getenv("ERP_LOGS_DIR", _DEFAULT_LOGS_DIR)
    return os.path.join(logs_dir, "retrieval")


# I am not using the logging-library because the proffast-pylot
# also uses that and figuring out how to not make these two
# interfere is not worth it

# the logfile name will have the time when the script has been started
logfile_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H-%M")


class Logger:
    def __init__(
        self,
        container_id: str,
        write_to_file: bool = True,
        print_to_console: bool = False,
    ) -> None:
        self.container_id = container_id
        self.logfile_name = f"{logfile_time}_{self.container_id}.log"
        self.retrieval_logs_dir = _get_retrieval_logs_dir()
        self.logfile_path = os.path.join(self.retrieval_logs_dir, self.logfile_name)
        self.write_to_file = write_to_file
        self.print_to_console = print_to_console

        os.makedirs(os.path.join(self.retrieval_logs_dir, "archive"), exist_ok=True)

    def _log(
        self,
        m: str,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "EXCEPTION"],
    ) -> None:
        t = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d %H:%M:%S")
        log_line = f"{t} - {level} - {m}\n"
        if self.write_to_file:
            with open(self.logfile_path, "a") as f:
                f.write(log_line)
        if self.print_to_console:
            print(log_line, end="")

    def exception(
        self,
        e: Exception,
        label: Optional[str] = None,
    ) -> None:
        """logs an exception and its traceback.

        exceptions will be formatted like this:

        ```txt
        (label, )ZeroDivisionError: division by zer
        --- details: -----------------
        ...
        --- traceback: ---------------
        ...
        ------------------------------
        ```
        """
        exception_name = traceback.format_exception_only(type(e), e)[0].strip()
        exception_traceback = "\n".join(
            traceback.format_exception(type(e), e, e.__traceback__)
        ).strip()
        exception_details = "None"
        if isinstance(e, tum_esm_utils.shell.CommandLineException) and (e.details is not None):
            exception_details = e.details.strip()

        subject_string = exception_name if label is None else f"{label}, {exception_name}"
        details_string = (
            f"--- details: -----------------\n{exception_details}\n"
            + f"--- traceback: ---------------\n{exception_traceback}\n"
            + "------------------------------"
        )

        self._log(f"{subject_string}\n{details_string}", "EXCEPTION")

    def error(self, m: str) -> None:
        self._log(m, "ERROR")

    def warning(self, m: str) -> None:
        self._log(m, "WARNING")

    def info(self, m: str) -> None:
        self._log(m, "INFO")

    def debug(self, m: str) -> None:
        self._log(m, "DEBUG")

    def horizontal_line(self, variant: str = "-") -> None:
        """
        log a horizontal line with 52 characters
        why 52? that is a very good question!
        """
        self._log(variant * 52, "INFO")

    def archive(self) -> None:
        """move the used log file into the archive"""
        archive_dir = os.path.join(
            self.retrieval_logs_dir,
            "archive",
            "main" if self.container_id == "main" else "containers",
        )
        os.makedirs(archive_dir, exist_ok=True)
        shutil.copyfile(
            self.logfile_path,
            os.path.join(archive_dir, self.logfile_name),
        )
        os.remove(self.logfile_path)
